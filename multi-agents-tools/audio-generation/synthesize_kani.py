#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chuyển bộ hội thoại text thành audio bằng Kani TTS Vie.
- Giữ nguyên logic manifest/metadata/resume như synthesize_vieneu.py.
- Không trộn nhãn: fraud và normal xuất ra thư mục riêng.
- Không trộn vai: left/right xuất ra thư mục con riêng.
- Loại bỏ phần mô tả cảm xúc trong ngoặc trước khi gửi TTS.
- Dùng 1 speaker_id (giọng Kani) cho toàn bộ dataset (có thể chỉnh qua --speaker_id).
- Có thể đọc trực tiếp merged_conversations.jsonl (đã ghép fraud + normal) hoặc cặp fraud/normal.
"""

import argparse
import csv
import json
import numpy as np
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from tqdm import tqdm
import soundfile as sf

# --------------------------------
# Text cleaning / parsing
# --------------------------------

PAREN_RE = re.compile(r"\([^)]*\)")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?！？。])\s+")
MAX_CHARS = 220  # giới hạn để tránh vượt context quá dài


def strip_stage_directions(text: str) -> str:
    """Loại bỏ phần mô tả trong ngoặc và thu gọn khoảng trắng."""
    cleaned = PAREN_RE.sub(" ", text)
    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Bỏ dấu ngoặc kép bọc ngoài nếu còn
    cleaned = cleaned.strip('"').strip()
    return cleaned


# --------------------------------
# Utterance & manifest
# --------------------------------

@dataclass
class Utterance:
    tts_id: str
    side: str  # "left" | "right"
    idx: int
    label: str  # "fraud" | "normal"
    text: str

    def filename(self) -> str:
        return f"{self.tts_id}_{self.side}_{self.idx:03d}.wav"


def load_jsonl(path: Path, label: str) -> Iterable[Utterance]:
    """Đọc fraud_conversations.jsonl / normal_conversations.jsonl."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            tts_id = data.get("tts_id")
            for i, msg in enumerate(data.get("left", [])):
                yield Utterance(
                    tts_id=tts_id,
                    side="left",
                    idx=i,
                    label=label,
                    text=strip_stage_directions(msg),
                )
            for i, msg in enumerate(data.get("right", [])):
                yield Utterance(
                    tts_id=tts_id,
                    side="right",
                    idx=i,
                    label=label,
                    text=strip_stage_directions(msg),
                )


def load_jsonl_merged(path: Path) -> Iterable[Utterance]:
    """Đọc merged_conversations.jsonl đã chứa cả label."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            tts_id = data.get("tts_id")
            label = data.get("label") or ("fraud" if data.get("is_fraud") else "normal")
            for i, msg in enumerate(data.get("left", [])):
                yield Utterance(
                    tts_id=tts_id,
                    side="left",
                    idx=i,
                    label=label,
                    text=strip_stage_directions(msg),
                )
            for i, msg in enumerate(data.get("right", [])):
                yield Utterance(
                    tts_id=tts_id,
                    side="right",
                    idx=i,
                    label=label,
                    text=strip_stage_directions(msg),
                )


def build_manifest(input_root: Path) -> list[Utterance]:
    """Tạo danh sách Utterance từ cặp fraud/normal JSONL dưới input_root."""
    fraud_file = next(input_root.glob("fraud_*/fraud_conversations.jsonl"), None)
    normal_file = next(input_root.glob("normal_*/normal_conversations.jsonl"), None)
    if not fraud_file or not normal_file:
        raise FileNotFoundError(
            "Không tìm thấy fraud_conversations.jsonl hoặc normal_conversations.jsonl dưới input_root"
        )

    utterances: list[Utterance] = []
    utterances.extend(load_jsonl(fraud_file, label="fraud"))
    utterances.extend(load_jsonl(normal_file, label="normal"))
    return utterances


# --------------------------------
# Kani TTS wrapper
# --------------------------------

class KaniTTSSynthesizer:
    """
    Thin-wrapper quanh Kani TTS Vie.
    - Import Kani từ repo ngoài (kani_root).
    - Khởi tạo model + normalizer.
    - Dùng chung 1 speaker_id cho mọi câu (có thể đổi bằng --speaker_id).
    """

    def __init__(
        self,
        kani_root: Path,
        speaker_id: str = "nam-mien-nam",
    ):
        self.kani_root = kani_root
        self.speaker_id = speaker_id
        self.sample_rate = 22050

        # Thêm path tới repo Kani vào sys.path để import được module
        sys.path.insert(0, str(kani_root))

        self._load_model()

    def _load_model(self):
        try:
            from kani_vie.tts_core import Config, KaniModel, NemoAudioPlayer  # type: ignore
            from utils.normalize_text import VietnameseTTSNormalizer  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "Không import được Kani TTS từ repo Kani-TTS-Vie. "
                "Hãy kiểm tra --kani_root (phải trỏ tới thư mục clone Kani-TTS-Vie)."
            ) from exc

        config = Config()
        player = NemoAudioPlayer(config)
        self.kani = KaniModel(config, player)
        self.normalizer = VietnameseTTSNormalizer()

    def _chunk_text(self, text: str) -> List[str]:
        """Tách text thành các đoạn ngắn để tránh vượt giới hạn context."""
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
                    # fallback: hard split theo độ dài
                    for i in range(0, len(p), MAX_CHARS):
                        chunks.append(p[i : i + MAX_CHARS].strip())
                    buffer = ""
        if buffer:
            chunks.append(buffer)
        return [c for c in chunks if c]

    def synthesize(self, text: str, out_path: Path):
        """Sinh audio cho 1 câu và lưu ra out_path."""
        out_path.parent.mkdir(parents=True, exist_ok=True)

        text = text.strip()
        if not text:
            # Câu rỗng -> ghi file trống để giữ alignment nếu cần
            sf.write(str(out_path), np.array([], dtype=np.float32), self.sample_rate)
            return

        segments = self._chunk_text(text)
        wavs = []

        for seg in segments:
            seg_norm = self.normalizer.normalize(seg)
            audio, _ = self.kani.run_model(seg_norm, speaker_id=self.speaker_id)
            wavs.append(audio.astype(np.float32))

        wav = np.concatenate(wavs) if len(wavs) > 1 else wavs[0]
        sf.write(str(out_path), wav, self.sample_rate)


# --------------------------------
# Metadata & synth loop (giữ nguyên logic)
# --------------------------------

def write_metadata(manifest: list[Utterance], output_root: Path, dataset_name: str, dry_run: bool):
    """
    Viết metadata.csv giống synthesize_vieneu.py:
    audio_path, text, tts_id, side, utt_idx, label
    """
    rows = []
    for utt in manifest:
        out_dir = output_root / dataset_name / utt.label / utt.side
        audio_path = out_dir / utt.filename()
        rows.append((audio_path, utt.text, utt.tts_id, utt.side, utt.idx, utt.label))

    meta_path = output_root / dataset_name / "metadata.csv"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["audio_path", "text", "tts_id", "side", "utt_idx", "label"])
        for audio_path, text, tts_id, side, idx, label in rows:
            writer.writerow([audio_path, text, tts_id, side, idx, label])

    if dry_run:
        print(f"[DRY-RUN] Metadata ghi tại: {meta_path} (không sinh audio)")
    else:
        print(f"Metadata ghi tại: {meta_path}")
    return rows


def synthesize_dataset(rows, synthesizer: KaniTTSSynthesizer, overwrite: bool = False):
    """
    Vòng lặp synth chính, giữ nguyên cơ chế resume:
    - Nếu file audio đã tồn tại và không có --overwrite thì bỏ qua.
    """
    for (audio_path, text, _, _, _, _) in tqdm(rows, desc="Synthesizing"):
        out_path = Path(audio_path)
        if out_path.exists() and not overwrite:
            continue
        try:
            synthesizer.synthesize(text, out_path)
        except Exception as exc:
            print(f"[ERR] {out_path.name}: {exc}")


# --------------------------------
# CLI
# --------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Sinh audio từ bộ hội thoại text bằng Kani TTS Vie"
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

    # Tham số Kani TTS
    parser.add_argument(
        "--kani_root",
        required=False,
        help=(
            "Đường dẫn tới repo Kani-TTS-Vie đã clone "
            "(vd: /content/Kani-TTS-Vie)"
        ),
    )
    parser.add_argument(
        "--speaker_id",
        default="nam-mien-nam",
        help="speaker_id của Kani TTS Vie (mặc định: nam-mien-nam)",
    )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Chỉ tạo metadata.csv, không chạy TTS",
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

    input_root = Path(args.input_root).resolve() if args.input_root else None
    output_root = Path(args.output_root).resolve()

    # Build manifest
    if args.input_file:
        manifest = list(load_jsonl_merged(Path(args.input_file)))
    else:
        manifest = build_manifest(input_root)

    # Viết metadata (giống file cũ)
    rows = write_metadata(manifest, output_root, dataset_name, args.dry_run)

    if args.dry_run:
        return

    if not args.kani_root:
        raise SystemExit("Cần truyền --kani_root khi không dùng --dry_run")

    synthesizer = KaniTTSSynthesizer(
        kani_root=Path(args.kani_root).resolve(),
        speaker_id=args.speaker_id,
    )

    synthesize_dataset(rows, synthesizer, overwrite=args.overwrite)
    print(f"Đã sinh audio vào {output_root / dataset_name}")


if __name__ == "__main__":
    main()
