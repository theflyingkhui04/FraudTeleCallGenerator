## Audio generation with VieNeu-TTS

This folder holds a small pipeline to turn the text conversations in `multi-agents-tools/text_dataset/...` into audio with the VieNeu‑TTS model (Hugging Face + voice cloning).

### Prerequisites
- Clone VieNeu‑TTS locally. In your setup it lives at:  
  `D:\Du-an\FraudTeleCallGenerator\multi-agents-tools\audio-generation\VieNeu-TTS`
- Install its dependencies as documented in that repo (Python ≥ 3.11, PyTorch, torchaudio, phonemizer/eSpeak NG, etc.).
- Make sure you can run the quickstart Python example from VieNeu‑TTS README.
- Pick one reference voice (audio + transcript) from `sample/` in VieNeu‑TTS, e.g.:
  - `sample/Vĩnh (nam miền Nam).wav` + `sample/Vĩnh (nam miền Nam).txt`
  - `sample/Đoan (nữ miền Nam).wav` + `sample/Đoan (nữ miền Nam).txt`

### What the script does

`synthesize_vieneu.py`:

- Reads fraud and normal JSONL files under a given text dataset root (expects:
  - `.../fraud_*/fraud_conversations.jsonl`
  - `.../normal_*/normal_conversations.jsonl`
- Cleans stage directions (text inside parentheses) so only spoken content is sent to TTS.
- Keeps labels separate (`fraud` vs `normal`) and sides separate (`left` vs `right`), saving to:

  ```
  voice_dataset/<dataset_name>/
    ├── fraud/
    │   ├── left/  tts_fraud_xxxxx_left_000.wav, ...
    │   └── right/
    └── normal/
        ├── left/
        └── right/
  ```

- Uses a single cloned voice for the whole dataset:
  - Loads VieNeu‑TTS via `from vieneu_tts import VieNeuTTS`
  - Encodes `--ref_audio` + `--ref_text` once (`encode_reference`)
  - Calls `infer(text, ref_codes, ref_text_raw)` per utterance
- Writes a `metadata.csv` with:

  ```text
  audio_path,text,tts_id,side,utt_idx,label
  ```

- Can run in `--dry_run` mode to only build `metadata.csv` (no audio), useful to verify structure.

### Usage example

```bash
cd multi-agents-tools/audio-generation

# 1) Dry run (no audio, just metadata/paths) to verify structure
python synthesize_vieneu.py ^
  --input_root ../text_dataset/balanced_dataset_20250908_111514 ^
  --output_root ../voice_dataset ^
  --dataset_name balanced_dataset_20250908_111514 ^
  --dry_run

# 2) Real synthesis using a reference voice from VieNeu-TTS "sample" folder
python synthesize_vieneu.py ^
  --input_root ../text_dataset/balanced_dataset_20250908_111514 ^
  --output_root ../voice_dataset ^
  --dataset_name balanced_dataset_20250908_111514 ^
  --vieneu_root "D:\Du-an\FraudTeleCallGenerator\multi-agents-tools\audio-generation\VieNeu-TTS" ^
  --backbone_repo pnnbao-ump/VieNeu-TTS ^
  --codec_repo neuphonic/neucodec ^
  --device auto ^
  --ref_audio "D:\Du-an\FraudTeleCallGenerator\multi-agents-tools\audio-generation\VieNeu-TTS\sample\Vĩnh (nam miền Nam).wav" ^
  --ref_text  "D:\Du-an\FraudTeleCallGenerator\multi-agents-tools\audio-generation\VieNeu-TTS\sample\Vĩnh (nam miền Nam).txt"
```

> Note: paths with spaces (e.g. `Vĩnh (nam miền Nam).wav`) must be quoted correctly in your shell.
> The script imports `VieNeuTTS` from your local clone, so `--vieneu_root` must point to the
> directory where `vieneu_tts/__init__.py` lives.
