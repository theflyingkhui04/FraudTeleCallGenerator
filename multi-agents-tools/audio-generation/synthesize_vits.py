#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh 1 file audio cho MỖI CUỘC GỌI bằng VITS (vits-tts-vietnamese, server.py).
- Đầu vào: fraud_conversations.jsonl / normal_conversations.jsonl (hoặc merged_conversations.jsonl).
- Mỗi tts_id -> 1 file wav: các lượt thoại left/right được chèn xen theo thứ tự.
- Giữ cơ chế metadata + resume: nếu file audio cuộc gọi đã tồn tại và không --overwrite thì bỏ qua.
"""

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import requests
import soundfile as sf
from tqdm import tqdm

# -----------------------------
# Text cleaning
# -----------------------------

PAREN_RE = re.compile(r"\([^)]*\)")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?！？。])\s+")
MAX_CHARS = 220  # tránh text quá dài 1 lần infer


def strip_stage_directions(text: str) -> str:
    """Loại bỏ phần mô tả trong ngoặc, chuẩn hoá khoảng trắng."""
    cleaned = PAREN_RE.sub(" ", text)
    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.strip('"').strip()
    return cleaned


# -----------------------------
# Data structure
# -----------------------------

@dataclass
class Dialogue:
    tts_id: str
    label: str  # fraud | normal
    left: List[str]
    right: List[str]


def load_dialogues_jsonl(path: Path, label: str) -> Iterable[Dialogue]:
    """
    Đọc fraud_conversations.jsonl / normal_conversations.jsonl
    Mỗi dòng = 1 cuộc gọi, chứa: tts_id, left: [...], right: [...]
    """
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            tts_id = data.get("tts_id")
            left = [strip_stage_directions(x) for x in data.get("left", [])]
            right = [strip_stage_directions(x) for x in data.get("right", [])]
            yield Dialogue(tts_id=tts_id, label=label, left=left, right=right)


def load_dialogues_merged(path: Path) -> Iterable[Dialogue]:
    """
    Đọc merged_conversations.jsonl: mỗi dòng có tts_id, label, left, right.
    """
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            tts_id = data.get("tts_id")
            label = data.get("label") or ("fraud" if data.get("is_fraud") else "normal")
            left = [strip_stage_directions(x) for x in data.get("left", [])]
            right = [strip_stage_directions(x) for x in data.get("right", [])]
            yield Dialogue(tts_id=tts_id, label=label, left=left, right=right)


def build_dialogues_from_root(input_root: Path) -> List[Dialogue]:
    """
    Xây list Dialogue từ thư mục input_root như pipeline cũ:
    - tìm fraud_*/fraud_conversations.jsonl
    - tìm normal_*/normal_conversations.jsonl
    """
    fraud_file = next(input_root.glob("fraud_*/fraud_conversations.jsonl"), None)
    normal_file = next(input_root.glob("normal_*/normal_conversations.jsonl"), None)
    if not fraud_file or not normal_file:
        raise FileNotFoundError(
            "Không tìm thấy fraud_conversations.jsonl hoặc normal_conversations.jsonl dưới input_root"
        )

    dialogues: List[Dialogue] = []
    dialogues.extend(load_dialogues_jsonl(fraud_file, label="fraud"))
    dialogues.extend(load_dialogues_jsonl(normal_file, label="normal"))
    return dialogues


# -----------------------------
# Tạo turns theo thứ tự hai bên chèn
# -----------------------------

def interleave_turns(dialogue: Dialogue, start_side: str = "left") -> List[Tuple[str, str]]:
    """
    Tạo list [(side, text)] theo thứ tự hội thoại:
    Giả định đơn giản: left[0] -> right[0] -> left[1] -> right[1] -> ...
    Nếu 1 bên hết câu thì bên còn lại nói hết phần còn lại.
    start_side: "left" hoặc "right"
    """
    left = dialogue.left
    right = dialogue.right
    i_left = 0
    i_right = 0
    n_left = len(left)
    n_right = len(right)
    turns: List[Tuple[str, str]] = []

    side = start_side
    while i_left < n_left or i_right < n_right:
        if side == "left":
            if i_left < n_left:
                turns.append(("left", left[i_left]))
                i_left += 1
            side = "right"
        else:
            if i_right < n_right:
                turns.append(("right", right[i_right]))
                i_right += 1
            side = "left"

        # Nếu 1 bên đã hết nhưng bên kia còn, cho bên kia nói hết
        if i_left >= n_left and i_right < n_right:
            while i_right < n_right:
                turns.append(("right", right[i_right]))
                i_right += 1
            break
        if i_right >= n_right and i_left < n_left:
            while i_left < n_left:
                turns.append(("left", left[i_left]))
                i_left += 1
            break

    return turns


# -----------------------------
# VITS TTS HTTP client
# -----------------------------

class VITSTTSSynthesizer:
    """
    Client gọi server VITS (vits-tts-vietnamese/server.py) qua HTTP.
    - /tts?text=...&speed=... -> JSON {hash, ...}
    - /audio/{hash}.wav -> file wav
    Dùng để synth từng câu, rồi ghép lại thành 1 file cho cả cuộc gọi.
    """

    def __init__(self, base_url: str = "http://localhost:8888", speed: str = "normal", timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.speed = speed
        self.timeout = timeout
        self.sample_rate = None  # set sau lần đầu decode wav

    def _chunk_text(self, text: str) -> List[str]:
        """Nếu câu quá dài, tách nhỏ để tránh server choke."""
        text = text.strip()
        if len(text) <= MAX_CHARS:
            return [text]

        parts = SENTENCE_SPLIT.split(text)
        chunks: List[str] = []
        buffer = ""
        for p in parts:
            if not p:
                continue
            candidate = (buffer + " " + p).strip() if buffer else p.strip()
            if len(candidate) <= MAX_CHARS:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                if len(p) <= MAX_CHARS:
                    buffer = p.strip()
                else:
                    for i in range(0, len(p), MAX_CHARS):
                        chunks.append(p[i : i + MAX_CHARS].strip())
                    buffer = ""
        if buffer:
            chunks.append(buffer)
        return [c for c in chunks if c]

    def _tts_call(self, text: str) -> np.ndarray:
        """Gọi /tts + /audio/hash.wav, trả về waveform float32."""
        tts_url = f"{self.base_url}/tts"
        params = {"text": text, "speed": self.speed}
        try:
            resp = requests.get(tts_url, params=params, timeout=self.timeout)
        except Exception as exc:
            raise RuntimeError(f"HTTP request tới {tts_url} thất bại: {exc}") from exc

        if resp.status_code != 200:
            raise RuntimeError(
                f"TTS server trả mã lỗi {resp.status_code}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except Exception as exc:
            raise RuntimeError(f"Response /tts không phải JSON hợp lệ: {resp.text[:200]}") from exc

        hash_id = data.get("hash")
        if not hash_id:
            raise RuntimeError(f"Response /tts thiếu 'hash': {data}")

        audio_url = f"{self.base_url}/audio/{hash_id}.wav"
        try:
            audio_resp = requests.get(audio_url, timeout=self.timeout)
        except Exception as exc:
            raise RuntimeError(f"HTTP request tới {audio_url} thất bại: {exc}") from exc

        if audio_resp.status_code != 200:
            raise RuntimeError(
                f"Audio server trả mã lỗi {audio_resp.status_code} cho {audio_url}"
            )

        import io
        bio = io.BytesIO(audio_resp.content)
        try:
            wav, sr = sf.read(bio, dtype="float32")
        except Exception as exc:
            raise RuntimeError(f"Không đọc được WAV từ {audio_url}: {exc}") from exc

        if self.sample_rate is None:
            self.sample_rate = sr
        return wav.astype(np.float32)

    def tts_text(self, text: str) -> np.ndarray:
        """TTS 1 câu (có thể chunk nếu dài), trả về waveform ghép."""
        if not text.strip():
            return np.zeros(0, dtype=np.float32)

        segments = self._chunk_text(text)
        wavs = []
        for seg in segments:
            wavs.append(self._tts_call(seg))
        if not wavs:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(wavs) if len(wavs) > 1 else wavs[0]

    def synthesize_dialogue(self, turns: List[Tuple[str, str]], out_path: Path):
        """
        Nhận list [(side, text)] theo thứ tự hội thoại,
        TTS từng text, ghép nối full audio, ghi ra out_path.
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)
        full_wavs = []
        for side, text in turns:
            wav = self.tts_text(text)
            if wav.size > 0:
                full_wavs.append(wav)

        if not full_wavs:
            # Không có câu nào -> file trống
            sr = self.sample_rate or 22050
            sf.write(str(out_path), np.zeros(0, dtype=np.float32), sr)
            return

        full = np.concatenate(full_wavs)
        sr = self.sample_rate or 22050
        sf.write(str(out_path), full, sr)


# -----------------------------
# Metadata + synth loop
# -----------------------------

def write_metadata(dialogues: List[Dialogue], output_root: Path, dataset_name: str, dry_run: bool):
    """
    Metadata cho MỖI CUỘC GỌI:
    - audio_path: path tới file wav
    - tts_id
    - label
    - num_left, num_right, num_total
    """
    rows = []
    for dlg in dialogues:
        out_dir = output_root / dataset_name / dlg.label
        audio_path = out_dir / f"{dlg.tts_id}.wav"
        num_left = len(dlg.left)
        num_right = len(dlg.right)
        num_total = num_left + num_right
        rows.append((audio_path, dlg.tts_id, dlg.label, num_left, num_right, num_total))

    meta_path = output_root / dataset_name / "metadata_dialogue.csv"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["audio_path", "tts_id", "label", "num_left", "num_right", "num_total"])
        for row in rows:
            writer.writerow(row)

    if dry_run:
        print(f"[DRY-RUN] Metadata ghi tại: {meta_path} (không synth audio)")
    else:
        print(f"Metadata ghi tại: {meta_path}")
    return rows


def synthesize_dataset(
    dialogues: List[Dialogue],
    rows_meta,
    synthesizer: VITSTTSSynthesizer,
    overwrite: bool = False,
    start_side: str = "left",
):
    """
    Vòng lặp synth:
    - Mỗi Dialogue -> 1 file wav cho cả cuộc gọi.
    - Nếu file đã tồn tại và không --overwrite -> skip (resume).
    """
    # rows_meta: [(audio_path, tts_id, label, num_left, num_right, num_total)]
    # map tts_id -> audio_path cho chắc
    id2path = {tts_id: audio_path for (audio_path, tts_id, *_rest) in rows_meta}

    for dlg in tqdm(dialogues, desc="Synthesizing dialogues"):
        out_path = Path(id2path[dlg.tts_id])
        if out_path.exists() and not overwrite:
            continue

        try:
            turns = interleave_turns(dlg, start_side=start_side)
            synthesizer.synthesize_dialogue(turns, out_path)
        except Exception as exc:
            print(f"[ERR] {dlg.tts_id}.wav: {exc}")


# -----------------------------
# CLI
# -----------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Sinh 1 file audio cho mỗi cuộc gọi bằng VITS (vits-tts-vietnamese)."
    )
    parser.add_argument(
        "--input_root",
        help="Thư mục dataset text (vd: ../text_dataset/balanced_dataset_YYYYMMDD_xxxxxx)",
    )
    parser.add_argument(
        "--input_file",
        help="Đường dẫn merged_conversations.jsonl (nếu có, sẽ bỏ qua input_root)",
    )
    parser.add_argument(
        "--output_root",
        default="../voice_dataset",
        help="Thư mục gốc để lưu audio (mặc định: ../voice_dataset)",
    )
    parser.add_argument(
        "--dataset_name",
        required=False,
        help=(
            "Tên dataset để lồng vào output_root (vd: balanced_dataset_YYYYMMDD_xxxxxx). "
            "Nếu không set và dùng --input_file, sẽ lấy tên thư mục chứa file."
        ),
    )

    # VITS server
    parser.add_argument(
        "--vits_base_url",
        default="http://localhost:8888",
        help="Base URL server VITS (mặc định: http://localhost:8888)",
    )
    parser.add_argument(
        "--speed",
        default="normal",
        help="Tốc độ nói: normal | fast | slow | very_fast (tuỳ server hỗ trợ)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout (giây) cho mỗi request HTTP (mặc định: 60)",
    )

    parser.add_argument(
        "--start_side",
        default="left",
        choices=["left", "right"],
        help="Giả định bên nào nói trước khi interleave: left hoặc right (mặc định: left)",
    )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Chỉ tạo metadata_dialogue.csv, không synth audio",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Ghi đè audio nếu đã tồn tại (mặc định: bỏ qua để resume)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.input_root and not args.input_file:
        raise SystemExit("Cần truyền --input_root hoặc --input_file")

    dataset_name = args.dataset_name
    if args.input_file and not dataset_name:
        dataset_name = Path(args.input_file).resolve().parent.name

    if not dataset_name:
        raise SystemExit("Cần --dataset_name (hoặc bỏ trống và dùng --input_file để tự suy ra).")

    output_root = Path(args.output_root).resolve()

    # Build dialogues
    if args.input_file:
        dialogues = list(load_dialogues_merged(Path(args.input_file)))
    else:
        input_root = Path(args.input_root).resolve()
        dialogues = build_dialogues_from_root(input_root)

    # Metadata (per dialogue)
    rows_meta = write_metadata(dialogues, output_root, dataset_name, args.dry_run)

    if args.dry_run:
        return

    synthesizer = VITSTTSSynthesizer(
        base_url=args.vits_base_url,
        speed=args.speed,
        timeout=args.timeout,
    )

    synthesize_dataset(
        dialogues,
        rows_meta,
        synthesizer,
        overwrite=args.overwrite,
        start_side=args.start_side,
    )

    print(f"Đã sinh audio hội thoại vào {output_root / dataset_name}")


if __name__ == "__main__":
    main()
