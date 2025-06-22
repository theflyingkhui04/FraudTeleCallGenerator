# Hướng dẫn sinh số lượng lớn hội thoại lừa đảo và bình thường

## 🎯 Mục tiêu
Tạo dataset lớn chứa hội thoại lừa đảo và bình thường để train model phát hiện lừa đảo viễn thông.

## 📂 Các script có sẵn

### 1. **batch_generate_dataset.py** - Script chính 
```bash
python batch_generate_dataset.py \
    --total_count 1000 \
    --fraud_ratio 0.5 \
    --api_key "your-api-key" \
    --base_url "https://api.siliconflow.cn/v1" \
    --mode balanced
```

**Tham số:**
- `--total_count`: Tổng số hội thoại (mặc định: 1000)
- `--fraud_ratio`: Tỷ lệ lừa đảo 0.0-1.0 (mặc định: 0.5 = 50%)
- `--mode`: balanced/fraud_only/normal_only
- `--output_dir`: Thư mục lưu kết quả

### 2. **optimized_generator.py** - Generator tối ưu
```bash
python optimized_generator.py \
    --fraud_count 500 \
    --normal_count 500 \
    --api_key "your-api-key" \
    --base_url "https://api.siliconflow.cn/v1" \
    --max_workers 3 \
    --delay 2
```

**Tính năng:**
- Parallel processing với ThreadPoolExecutor
- Retry logic cho rate limit
- Exponential backoff
- Progress tracking với tqdm

### 3. **mass_generate.ps1** - Script PowerShell cho Windows
```powershell
.\mass_generate.ps1 -TotalCount 2000 -ApiKey "your-key" -BaseUrl "your-url"
```

### 4. **mass_generate.sh** - Script Bash cho Linux/Mac  
```bash
./mass_generate.sh "your-api-key" "your-base-url" 2000
```

## 🚀 Cách sử dụng nhanh

### Tạo 1000 hội thoại cân bằng (500 fraud + 500 normal)
```bash
python batch_generate_dataset.py \
    --total_count 1000 \
    --fraud_ratio 0.5 \
    --api_key "sk-your-key" \
    --base_url "https://api.siliconflow.cn/v1" \
    --mode balanced
```

### Chỉ tạo hội thoại lừa đảo
```bash
python batch_generate_dataset.py \
    --total_count 500 \
    --api_key "sk-your-key" \
    --base_url "https://api.siliconflow.cn/v1" \
    --mode fraud_only
```

### Chỉ tạo hội thoại bình thường
```bash
python batch_generate_dataset.py \
    --total_count 500 \
    --api_key "sk-your-key" \
    --base_url "https://api.siliconflow.cn/v1" \
    --mode normal_only
```

## 📊 Cấu trúc kết quả

### Thư mục output:
```
balanced_dataset_20250620_143022/
├── fraud/
│   ├── fraud_dialogues_20250620_143022.jsonl
│   └── full_dialogues/
│       ├── fraud_00001.json
│       ├── fraud_00002.json
│       └── ...
├── normal/
│   ├── normal_dialogues_20250620_143022.jsonl
│   └── full_dialogues/
│       ├── normal_00001.json
│       └── ...
├── merged_dataset_20250620_143022.jsonl
└── dataset_stats_20250620_143022.json
```

### Định dạng JSONL:
```json
{
  "dialogue_id": "fraud_00001",
  "left": ["Xin chào, tôi là từ công an...", "Bạn cần hợp tác..."],
  "right": ["Vâng ạ", "Tôi không hiểu..."],
  "label": "fraud",
  "is_fraud": 1,
  "fraud_type": "Giả danh công an",
  "user_age": 45,
  "user_awareness": "thấp",
  "occupation": "người nghỉ hưu",
  "termination_reason": "Người dùng cung cấp thông tin",
  "terminator": "right"
}
```

## ⚙️ Tối ưu hóa hiệu suất

### 1. **Parallel Processing**
- Sử dụng `--max_workers 3-5` (không quá cao để tránh rate limit)
- Mỗi worker xử lý một hội thoại song song

### 2. **Rate Limiting**  
- `--delay 2-5` giây giữa các request
- Retry logic với exponential backoff
- Xử lý HTTP 429 (Too Many Requests)

### 3. **Batch Processing**
- Chia dataset lớn thành các batch nhỏ (100-200 hội thoại/batch)
- Tránh timeout và memory issues
- Dễ dàng recovery khi có lỗi

### 4. **Memory Management**
- Lưu kết quả ngay sau khi tạo xong
- Không giữ toàn bộ dataset trong memory
- Streaming write to JSONL

## 🎛️ Cấu hình cho từng use case

### Dataset nhỏ (100-500 hội thoại)
```bash
python batch_generate_dataset.py \
    --total_count 200 \
    --max_workers 3 \
    --delay 2
```

### Dataset trung bình (500-2000 hội thoại) 
```bash
python optimized_generator.py \
    --fraud_count 1000 \
    --normal_count 1000 \
    --max_workers 2 \
    --delay 3
```

### Dataset lớn (2000+ hội thoại)
```bash
# Sử dụng script mass_generate với batch processing
.\mass_generate.ps1 -TotalCount 5000
```

## 📈 Monitoring và Logging

### Log files:
- `dataset_generation_TIMESTAMP.log`: Log chi tiết quá trình
- `run.log`: Log từ các script generate_dialogues.py
- Console output với progress bars

### Thống kê realtime:
- Success/error rate
- Phân bố theo fraud_type, occupation, age, awareness
- Thời gian hoàn thành ước tính

## ⚠️ Lưu ý quan trọng

### 1. **API Limits**
- Kiểm tra rate limit của API provider
- Sử dụng delay phù hợp (2-5 giây)
- Monitor HTTP 429 errors

### 2. **Cost Management**
- Estimate cost: số hội thoại × tokens per dialogue × API rate
- Sử dụng batch size nhỏ để test trước
- Monitor spending realtime

### 3. **Quality Control**
- Kiểm tra sample kết quả trước khi chạy large batch
- Validate format và content
- Check termination reasons

### 4. **Recovery & Resume**
- Script hỗ trợ resume từ batch bị dở
- Backup intermediate results
- Error handling và retry logic

## 🔧 Troubleshooting

### Lỗi thường gặp:

1. **Rate limit (429)**
   - Tăng delay parameter
   - Giảm max_workers
   - Sử dụng exponential backoff

2. **API timeout**
   - Kiểm tra network connection
   - Tăng retry attempts
   - Sử dụng batch processing

3. **Memory issues**
   - Giảm batch size
   - Streaming processing
   - Clear cache periodically

4. **Invalid JSON output**
   - Kiểm tra prompt format
   - Validate AI response
   - Fallback parsing logic

## 🎯 Best Practices

1. **Start Small**: Test với 10-20 hội thoại trước
2. **Monitor Progress**: Sử dụng progress bars và logging
3. **Backup Frequently**: Lưu intermediate results
4. **Quality First**: Kiểm tra chất lượng trước quantity
5. **Cost Awareness**: Estimate và monitor cost
6. **Diverse Data**: Đảm bảo đa dạng về fraud_type, age, occupation
