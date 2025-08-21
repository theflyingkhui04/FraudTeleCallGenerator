# Dataset Generator - Hệ thống sinh dataset hội thoại lừa đảo viễn thông

## Mô tả
Hệ thống tích hợp sinh dataset hội thoại lừa đảo viễn thông và hội thoại bình thường, tạo ra bộ dữ liệu cân bằng để training model phát hiện lừa đảo.

## Cấu trúc thư mục
```
generator/
├── dataset_generator.py    # Script chính sinh dataset
└── README.md             # Hướng dẫn sử dụng

dataset/                  # Thư mục chứa dataset được sinh
├── fraud_YYYYMMDD_HHMMSS/
├── normal_YYYYMMDD_HHMMSS/
├── balanced_dataset_YYYYMMDD_HHMMSS/
├── generator_log_YYYYMMDD_HHMMSS.log
└── generation_results_YYYYMMDD_HHMMSS.json
```

## Tính năng

### 1. Sinh dataset cân bằng
- Tự động tạo dataset với tỷ lệ lừa đảo/bình thường tùy chỉnh
- Gộp và trộn ngẫu nhiên các hội thoại
- Thêm nhãn và metadata cho từng hội thoại

### 2. Sinh dataset chuyên biệt
- Chỉ sinh hội thoại lừa đảo
- Chỉ sinh hội thoại bình thường
- Tùy chỉnh số lượng theo nhu cầu

### 3. Thống kê và phân tích
- Thống kê phân bố loại lừa đảo
- Phân tích demographics người dùng
- Đánh giá chất lượng hội thoại (số turn, độ dài)

### 4. Quản lý và theo dõi
- Log chi tiết quá trình sinh
- Lưu kết quả và cấu hình
- Timestamp để quản lý phiên bản

## Cài đặt và sử dụng

### Yêu cầu
- Python 3.8+
- Các module: `pathlib`, `subprocess`, `logging`, `argparse`
- API key và endpoint LLM (SiliconFlow, OpenAI, Google Gemini v.v.)

### 1. Cách sử dụng cơ bản

#### Sinh dataset cân bằng
```bash
# Sinh 1000 hội thoại cân bằng (50% lừa đảo, 50% bình thường)
python dataset_generator.py --total 1000 \
  --api_key "your_api_key" \
  --model "tên model" \
  --base_url "https://api.siliconflow.cn/v1"

# Sinh 500 hội thoại với 70% lừa đảo
python dataset_generator.py --total 500 --fraud_ratio 0.7 \
  --api_key "your_api_key" \
  --base_url "https://api.siliconflow.cn/v1"
```

#### Sinh dataset chuyên biệt
```bash
# Chỉ sinh 300 hội thoại lừa đảo
python dataset_generator.py --fraud_only 300 \
  --api_key "your_api_key" \
  --base_url "https://api.siliconflow.cn/v1"

# Chỉ sinh 200 hội thoại bình thường
python dataset_generator.py --normal_only 200 \
  --api_key "your_api_key" \
  --base_url "https://api.siliconflow.cn/v1"
```

### 2. Sử dụng script nhanh
```bash
# Chạy với cấu hình có sẵn
python quick_generate.py
```

### 3. Tham số chi tiết

| Tham số | Mô tả | Mặc định |
|---------|-------|----------|
| `--total` | Tổng số hội thoại cần sinh | - |
| `--fraud_only` | Chỉ sinh hội thoại lừa đảo | - |
| `--normal_only` | Chỉ sinh hội thoại bình thường | - |
| `--fraud_ratio` | Tỷ lệ hội thoại lừa đảo (0.0-1.0) | 0.5 |
| `--api_key` | API key (bắt buộc) | - |
| `--base_url` | Base URL API (bắt buộc) | - |
| `--model` | Model AI | deepseek-ai/DeepSeek-V2.5 |

## Kết quả đầu ra

### 1. Cấu trúc file dataset
```json
{
  "dialogue": [
    {"speaker": "Caller", "content": "Xin chào, tôi là từ cảnh sát..."},
    {"speaker": "Victim", "content": "Dạ, có gì ạ?"},
    ...
  ],
  "fraud_type": "impersonation_police",
  "user_age": 45,
  "user_awareness": "low",
  "occupation": "housewife",
  "label": "fraud",
  "is_fraud": 1,
  "timestamp": "2025-06-20T20:30:15"
}
```

### 2. File thống kê
```json
{
  "generation_info": {
    "timestamp": "20250620_203015",
    "total_conversations": 1000,
    "model": "deepseek-ai/DeepSeek-V2.5"
  },
  "label_distribution": {"fraud": 500, "normal": 500},
  "fraud_types": {
    "impersonation_police": 85,
    "fake_bank_call": 92,
    "tech_support_scam": 73,
    ...
  },
  "user_demographics": {
    "age_groups": {"18-25": 150, "26-40": 300, ...},
    "occupations": {"student": 120, "employee": 280, ...},
    "awareness_levels": {"low": 250, "medium": 500, "high": 250}
  },
  "conversation_quality": {
    "avg_turns": 12.5,
    "avg_length": 1250.3
  }
}
```

## Tích hợp với hệ thống hiện tại

Generator tự động gọi các script hiện có:
- `../FraudTeleCallGenerator/generate_dialogues.py` - Sinh hội thoại lừa đảo
- `../NormalTeleCallGenerator/generate_normal_dialogues.py` - Sinh hội thoại bình thường

Đảm bảo các script này hoạt động đúng với tham số:
- `--count`: Số lượng hội thoại
- `--output`: File đầu ra
- `--full_output_dir`: Thư mục hội thoại đầy đủ
- `--api_key`, `--base_url`, `--model`: Cấu hình API
- `--workers`: Số worker song song
- `--max_turns`: Số turn tối đa

## Xử lý lỗi và debug

### 1. Kiểm tra log
```bash
# Xem log chi tiết
tail -f ../dataset/generator_log_20250620_203015.log
```

### 2. Lỗi thường gặp

#### Lỗi API
```
❌ Lỗi sinh hội thoại lừa đảo: 
STDERR: API key invalid
```
**Giải pháp**: Kiểm tra API key và endpoint

#### Lỗi script không tìm thấy
```
❌ Exception sinh hội thoại: No such file
```
**Giải pháp**: Kiểm tra đường dẫn script và cấu trúc thư mục

#### Lỗi thiếu tham số
```
❌ Lỗi: unrecognized arguments: --max_workers
```
**Giải pháp**: Cập nhật script con để hỗ trợ tham số mới

### 3. Test script con
```bash
# Test script lừa đảo
cd ../FraudTeleCallGenerator
python generate_dialogues.py --count 1 --output test.jsonl \
  --full_output_dir test_full --api_key KEY --base_url URL --model MODEL

# Test script bình thường  
cd ../NormalTeleCallGenerator
python generate_normal_dialogues.py --count 1 --output test.jsonl \
  --full_output_dir test_full --api_key KEY --base_url URL --model MODEL
```

## Mở rộng và tùy chỉnh

### 1. Thêm loại hội thoại mới
- Cập nhật script con để hỗ trợ loại mới
- Thêm mapping trong `create_dataset_statistics()`

### 2. Tùy chỉnh format đầu ra
- Sửa `merge_and_balance_dataset()` để thay đổi format
- Thêm trường metadata tùy chỉnh

### 3. Batch processing lớn
```python
# Sinh nhiều dataset nhỏ rồi gộp lại
for i in range(10):
    subprocess.run([
        "python", "dataset_generator.py", 
        "--total", "100", "--api_key", key, "--base_url", url
    ])
```

## Performance và tối ưu

### 1. Thời gian sinh
- Dataset 100 hội thoại: ~5-10 phút
- Dataset 500 hội thoại: ~25-50 phút  
- Dataset 1000 hội thoại: ~50-100 phút

### 2. Tối ưu tốc độ
- Tăng `--workers` trong script con
- Sử dụng API endpoint nhanh hơn
- Sinh parallel nhiều batch nhỏ

### 3. Quản lý tài nguyên
- Giám sát RAM và disk space
- Rate limiting để tránh quota API
- Backup định kỳ dataset quan trọng

## Troubleshooting

### Q: Script không chạy được?
A: Kiểm tra:
1. Python path và version
2. Working directory
3. File permissions
4. API credentials

### Q: Dataset bị lỗi format?
A: Kiểm tra:
1. Encoding UTF-8
2. JSON format trong script con
3. Line endings consistency

### Q: Thống kê không chính xác?
A: Kiểm tra:
1. Mapping field names
2. Data types consistency  
3. Missing value handling

### Q: Memory issues với dataset lớn?
A: Sử dụng:
1. Streaming processing
2. Batch smaller chunks
3. Cleanup temporary files

## Liên hệ và hỗ trợ
- Xem log chi tiết trong `../dataset/`
- Kiểm tra file `generation_results_*.json`
- Debug từng script con riêng lẻ
