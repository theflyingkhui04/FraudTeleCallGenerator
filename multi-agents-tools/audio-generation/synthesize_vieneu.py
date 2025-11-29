#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chuyển bộ hội thoại text thành audio bằng VieNeu-TTS (Hugging Face API, voice cloning).
- Không trộn nhãn: fraud và normal xuất ra thư mục riêng.
- Không trộn vai: left/right xuất ra thư mục con riêng.
- Loại bỏ phần mô tả cảm xúc trong ngoặc trước khi gửi TTS.
- Dùng 1 giọng tham chiếu (voice cloning) cho toàn bộ dataset.
- Có thể đọc trực tiếp merged_conversations.jsonl (đã ghép fraud + normal) hoặc cặp fraud/normal.
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from tqdm import tqdm
import soundfile as sf
import torch

PAREN_RE = re.compile(r"\([^)]*\)")


def strip_stage_directions(text: str) -> str:
    """Loại bỏ phần mô tả trong ngoặc và thu gọn khoảng trắng."""
    cleaned = PAREN_RE.sub(" ", text)
    cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Bỏ dấu ngoặc kép bọc ngoài nếu còn
    cleaned = cleaned.strip('"').strip()
    return cleaned


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
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            tts_id = data.get("tts_id")
            for i, msg in enumerate(data.get("left", [])):
                yield Utterance(tts_id=tts_id, side="left", idx=i, label=label, text=strip_stage_directions(msg))
            for i, msg in enumerate(data.get("right", [])):
                yield Utterance(tts_id=tts_id, side="right", idx=i, label=label, text=strip_stage_directions(msg))


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
                yield Utterance(tts_id=tts_id, side="left", idx=i, label=label, text=strip_stage_directions(msg))
            for i, msg in enumerate(data.get("right", [])):
                yield Utterance(tts_id=tts_id, side="right", idx=i, label=label, text=strip_stage_directions(msg))


class VieNeuTTSSynthesizer:
    """
    Thin-wrapper quanh VieNeuTTS (Hugging Face).
    - Khởi tạo 1 model.
    - Encode 1 voice reference (audio + transcript).
    - Dùng chung ref_codes + ref_text_raw cho mọi câu.
    """

    def __init__(
        self,
        vieneu_root: Path,
        backbone_repo: str,
        codec_repo: str,
        device: str,
        ref_audio: Path,
        ref_text: Path,
    ):
        self.vieneu_root = vieneu_root
        self.backbone_repo = backbone_repo
        self.codec_repo = codec_repo
        self.device = device
        self.ref_audio = ref_audio
        self.ref_text = ref_text

        sys.path.insert(0, str(vieneu_root))
        self._load_model_and_reference()

    def _load_model_and_reference(self):
        try:
            from vieneu_tts import VieNeuTTS  # type: ignore
        except Exception as exc:  # pragma: no cover - informative error path
            raise RuntimeError(
                "Không import được VieNeuTTS từ repo VieNeu-TTS. "
                "Hãy kiểm tra --vieneu_root (phải trỏ tới thư mục clone VieNeu-TTS)."
            ) from exc

        device = self.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"

        # Khởi tạo model theo quickstart trong README VieNeu-TTS
        self.tts = VieNeuTTS(
            backbone_repo=self.backbone_repo,
            backbone_device=device,
            codec_repo=self.codec_repo,
            codec_device=device,
        )

        # Đọc text tham chiếu
        self.ref_text_raw = self.ref_text.read_text(encoding="utf-8")

        # Encode reference audio một lần
        print(f"Encoding reference audio từ: {self.ref_audio}")
        self.ref_codes = self.tts.encode_reference(str(self.ref_audio))

    def synthesize(self, text: str, out_path: Path):
        """Sinh audio cho 1 câu và lưu ra out_path."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not text.strip():
            # Bỏ qua câu rỗng, vẫn tạo file trống để giữ alignment nếu cần
            sf.write(str(out_path), [], 24000)
            return

        try:
            wav = self.tts.infer(text, self.ref_codes, self.ref_text_raw)
            sf.write(str(out_path), wav, 24000)
        except Exception as exc:  # pragma: no cover - runtime failure surface
            raise RuntimeError(f"TTS lỗi với văn bản: {text[:80]}...") from exc


def build_manifest(input_root: Path) -> List[Utterance]:
    fraud_file = next(input_root.glob("fraud_*/fraud_conversations.jsonl"), None)
    normal_file = next(input_root.glob("normal_*/normal_conversations.jsonl"), None)
    if not fraud_file or not normal_file:
        raise FileNotFoundError(
            "Không tìm thấy fraud_conversations.jsonl hoặc normal_conversations.jsonl dưới input_root"
        )

    utterances: List[Utterance] = []
    utterances.extend(load_jsonl(fraud_file, label="fraud"))
    utterances.extend(load_jsonl(normal_file, label="normal"))
    return utterances


def write_metadata(manifest: List[Utterance], output_root: Path, dataset_name: str, dry_run: bool):
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


def synthesize_dataset(rows, synthesizer: VieNeuTTSSynthesizer):
    for (audio_path, text, _, _, _, _) in tqdm(rows, desc="Synthesizing"):
        out_path = Path(audio_path)
        synthesizer.synthesize(text, out_path)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sinh audio từ bộ hội thoại text bằng VieNeu-TTS (Hugging Face API + voice cloning)"
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
        help="Tên dataset để lồng vào output_root (vd: balanced_dataset_YYYYMMDD_xxxxxx). Nếu không set và dùng --input_file, sẽ lấy tên thư mục chứa file.",
    )

    # Tham số VieNeu-TTS
    parser.add_argument(
        "--vieneu_root",
        required=False,
        help="Đường dẫn tới repo VieNeu-TTS đã clone (vd: D:/Du-an/FraudTeleCallGenerator/multi-agents-tools/audio-generation/VieNeu-TTS)",
    )
    parser.add_argument(
        "--backbone_repo",
        default="pnnbao-ump/VieNeu-TTS",
        help="Tên repo backbone trên Hugging Face (mặc định: pnnbao-ump/VieNeu-TTS)",
    )
    parser.add_argument(
        "--codec_repo",
        default="neuphonic/neucodec",
        help="Tên repo codec trên Hugging Face (mặc định: neuphonic/neucodec)",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Thiết bị chạy model (auto: cuda nếu có, ngược lại cpu)",
    )
    parser.add_argument(
        "--ref_audio",
        help="Đường dẫn file wav tham chiếu để clone giọng",
    )
    parser.add_argument(
        "--ref_text",
        help="Đường dẫn file txt transcript tương ứng với ref_audio",
    )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Chỉ tạo metadata.csv, không chạy VieNeu-TTS",
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

    if args.input_file:
        manifest = list(load_jsonl_merged(Path(args.input_file)))
    else:
        manifest = build_manifest(input_root)

    rows = write_metadata(manifest, output_root, dataset_name, args.dry_run)

    if args.dry_run:
        return

    if not args.vieneu_root:
        raise SystemExit("Cần truyền --vieneu_root khi không dùng --dry_run")

    if not (args.ref_audio and args.ref_text):
        raise SystemExit("Cần truyền cả --ref_audio và --ref_text để dùng voice cloning của VieNeu-TTS")

    synthesizer = VieNeuTTSSynthesizer(
        vieneu_root=Path(args.vieneu_root).resolve(),
        backbone_repo=args.backbone_repo,
        codec_repo=args.codec_repo,
        device=args.device,
        ref_audio=Path(args.ref_audio).resolve(),
        ref_text=Path(args.ref_text).resolve(),
    )

    synthesize_dataset(rows, synthesizer)
    print(f"Đã sinh audio vào {output_root / dataset_name}")


if __name__ == "__main__":
    main()
