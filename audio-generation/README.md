# 🎵 TeleAntiFraud Audio Generation

Chuyển đổi dataset text thành audio sử dụng VITS Vietnamese TTS cho dự án TeleAntiFraud.

## 🚀 Cài đặt

### 1. Cài đặt dependencies
```bash
cd audio-generation
pip install -r requirements.txt
```

### 2. Thiết lập VITS models
```bash
python setup_vits.py
```

### 3. Test TTS
```bash
python vits_client.py
```

## 🎯 Sử dụng

### Chuyển đổi dataset thành audio
```bash
python dataset_to_audio.py --dataset ../multi-agents-tools/dataset/balanced_dataset_20250704_030451/merged_conversations.jsonl --output audio_output --limit 10
```

### Tham số:
- `--dataset`: Đường dẫn đến file JSONL dataset
- `--output`: Thư mục output (mặc định: audio_dataset)
- `--models`: Đường dẫn đến models VITS (mặc định: models)
- `--workers`: Số workers song song (mặc định: 2)
- `--limit`: Giới hạn số conversation (để test)

## 📊 Cấu trúc output

```
audio_dataset/
├── conv_00000/
│   ├── msg_000_scammer.wav
│   ├── msg_001_victim.wav
│   ├── msg_002_scammer.wav
│   └── metadata.json
├── conv_00001/
│   └── ...
└── generation_summary.json
```

## 🎭 Voice Configuration

### Scammer (Kẻ lừa đảo):
- **Giọng**: Nam
- **Cảm xúc**: Tự tin, uy quyền, thuyết phục
- **Tốc độ**: Bình thường (1.0)

### Victim (Nạn nhân):
- **Giọng**: Nữ
- **Cảm xúc**: Lo lắng, hoang mang, sợ hãi
- **Tốc độ**: Chậm hơn (0.85-0.9)

## 🎨 Emotion Detection

Hệ thống tự động nhận diện cảm xúc từ nội dung text:

### Scammer:
- **Confident**: "tôi gọi từ", "chúng tôi", "cơ quan"
- **Authoritative**: "bạn phải", "yêu cầu", "bắt buộc"
- **Persuasive**: "tin tôi", "yên tâm", "đảm bảo"

### Victim:
- **Worried**: "lo lắng", "sợ", "hoang mang"
- **Confused**: "sao", "tại sao", "làm sao"
- **Scared**: "trời ơi", "không thể", "chết rồi"

## 📈 Performance

- **Tốc độ**: ~5-10 giây/conversation (tùy độ dài)
- **Chất lượng**: 22050 Hz, 16-bit WAV
- **Parallel processing**: 2 workers mặc định (tránh overload)

## 🔧 Troubleshooting

### 1. Lỗi model không tải được:
```bash
# Tải manual từ HuggingFace
wget https://huggingface.co/capleaf/viXTTS/resolve/main/model.pth -O models/vits_viet_female.pth
```

### 2. Lỗi CUDA out of memory:
```bash
# Chạy trên CPU
python dataset_to_audio.py --dataset ... --workers 1
```

### 3. Lỗi phonemizer:
```bash
# Cài đặt espeak
# Ubuntu: sudo apt-get install espeak espeak-data
# Windows: Download from http://espeak.sourceforge.net/download.html
```

## 📝 Logs

- Tiến trình được log trong console
- Metadata chi tiết cho mỗi conversation
- Summary tổng quan sau khi hoàn thành

## 🎉 Kết quả

Sau khi chạy xong, bạn sẽ có:
- Audio files cho từng message
- Metadata JSON với thông tin chi tiết
- Summary report về tiến trình generation
- Cấu trúc thư mục organized theo conversation

## 🔮 Tương lai

- [ ] Thêm nhiều giọng địa phương
- [ ] Fine-tune emotion detection
- [ ] Optimize tốc độ generation
- [ ] Thêm background noise cho thực tế hơn
- [ ] Integration với dataset generation pipeline
