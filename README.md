
# TeleAntiFraud: Hệ thống phát hiện lừa đảo qua điện thoại

Hệ thống AI đa tác nhân để tạo dataset hội thoại lừa đảo qua điện thoại phục vụ nghiên cứu và phát triển mô hình phát hiện gian lận viễn thông.

## Giới thiệu

TeleAntiFraud là dự án nghiên cứu sử dụng AI để tạo ra dataset hội thoại mô phỏng các cuộc gọi lừa đảo và bình thường. Hệ thống giúp phát triển các mô hình phát hiện lừa đảo hiệu quả cho ngành viễn thông.

### Tính năng chính

- **Tạo hội thoại tự động**: Sử dụng nhiều AI agent để mô phỏng các cuộc hội thoại thực tế
- **15+ loại lừa đảo**: Bao gồm các hình thức lừa đảo phổ biến tại Việt Nam
- **Dataset cân bằng**: Tự động tạo cả hội thoại lừa đảo và bình thường
- **Định dạng chuẩn**: Output JSONL với metadata đầy đủ
- **Tích hợp API**: Hỗ trợ Gemini, OpenAI và các LLM khác

## Kiến trúc hệ thống

Hệ thống sử dụng 4 thành phần chính:

- **Left Agent**: Đóng vai kẻ lừa đảo, tạo các chiến thuật lừa đảo
- **Right Agent**: Đóng vai nạn nhân với các mức độ cảnh giác khác nhau
- **Manager Agent**: Giám sát và quyết định khi nào kết thúc hội thoại
- **Dialogue Orchestrator**: Điều phối toàn bộ cuộc hội thoại

## Cách sử dụng

### Cài đặt

```bash
# Cài đặt dependencies
pip install -r requirements.txt
```

### Tạo dataset

```bash
# Di chuyển đến thư mục generator
cd multi-agents-tools/generator

# Tạo dataset cân bằng
python dataset_generator.py \
    --total 100 \
    --api_key "your-gemini-api-key" \
    --model "gemini-2.0-flash"
```

### Kết quả

```
dataset/balanced_dataset_20250622_170832/
├── fraud_conversations.jsonl     # Hội thoại lừa đảo
├── normal_conversations.jsonl    # Hội thoại bình thường
└── merged_conversations.jsonl    # Dataset tổng hợp
```

## Các loại lừa đảo được hỗ trợ

| Loại | Mô tả |
|------|-------|
| Đầu tư | Lừa đảo crypto, forex, chứng khoán |
| Tình cảm | Lừa đảo qua mạng xã hội, hẹn hò |
| Phishing | Giả mạo website, đánh cắp thông tin |
| Trúng thưởng | Giả mạo trúng số, quà tặng |
| Việc làm | Tuyển dụng giả, làm việc tại nhà |
| Mạo danh | Giả mạo cảnh sát, ngân hàng, cơ quan |

## Cấu trúc dự án

```
TeleAntiFraud/
├── multi-agents-tools/
│   ├── AntiFraudMatrix/          # Tạo hội thoại lừa đảo
│   ├── AntiFraudMatrix-normal/   # Tạo hội thoại bình thường
│   └── generator/                # Generator tổng hợp
├── README.md
└── .gitignore
```

## Ví dụ output

```json
{
  "tts_id": "tts_fraud_00001",
  "left": ["Chào anh, tôi gọi từ ngân hàng...", "Tài khoản anh có giao dịch lạ..."],
  "right": ["Vâng ạ, có chuyện gì vậy?", "Thật sao? Tôi không làm gì cả..."],
  "user_age": 45,
  "user_awareness": "thấp", 
  "fraud_type": "Ngân hàng",
  "occupation": "Người nghỉ hưu",
  "label": "fraud",
  "is_fraud": 1
}
```

## Hiệu suất

- Tốc độ: 2-3 hội thoại/phút
- Tỷ lệ thành công: 95%+ hội thoại hợp lệ
- Hỗ trợ xử lý song song
- Tích hợp nhiều API LLM

## Tài liệu

- [Hướng dẫn tạo dataset](multi-agents-tools/AntiFraudMatrix/DATASET_GENERATION_GUIDE.md)

## Giấy phép

Dự án sử dụng giấy phép MIT.