#!/bin/bash

# Script sinh hội thoại bình thường
# Cách dùng ví dụ: ./run_normal.sh 10

# Thiết lập giá trị mặc định
DEFAULT_COUNT=100
DEFAULT_MODEL="Qwen/Qwen2.5-72B-Instruct"
DEFAULT_WORKERS=2
API_KEY="sk-fpwiniyhjwughnzrzdckrrkiyxkebpgcoslhnenybgbxyvva"
BASE_URL="https://api.siliconflow.cn/v1"

# Lấy timestamp hiện tại
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Xử lý tham số dòng lệnh
COUNT=${1:-$DEFAULT_COUNT}
MODEL=${2:-$DEFAULT_MODEL}
WORKERS=${3:-$DEFAULT_WORKERS}

# Thiết lập tên file xuất kết quả
OUTPUT_FILE="results/normal_dialogues-${TIMESTAMP}.jsonl"
FULL_OUTPUT_DIR="results/full_normal_dialogues_${TIMESTAMP}"

echo "====================================="
echo "Bắt đầu sinh hội thoại bình thường"
echo "====================================="
echo "Số lượng cần tạo: $COUNT"
echo "Mô hình sử dụng: $MODEL"
echo "Luồng xử lý song song: $WORKERS"
echo "Tệp đầu ra: $OUTPUT_FILE"
echo "Thư mục đầu ra đầy đủ: $FULL_OUTPUT_DIR"
echo "Thời gian bắt đầu: $(date)"
echo "====================================="

# Create log directory
mkdir -p logs

# Chạy lệnh và ghi log
python generate_normal_dialogues.py \
  --count $COUNT \
  --base_url "$BASE_URL" \
  --api_key "$API_KEY" \
  --model "$MODEL" \
  --workers $WORKERS \
  --output "$OUTPUT_FILE" \
  --full_output_dir "$FULL_OUTPUT_DIR" 2>&1 | tee "logs/generate_normal_${TIMESTAMP}.log"

# Check command execution status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "====================================="
  echo "Quá trình tạo đối thoại đã hoàn thành thành công!"
  echo "Thời gian kết thúc: $(date)"
  echo "Tệp đầu ra: $OUTPUT_FILE"
  echo "Thư mục đối thoại đầy đủ: $FULL_OUTPUT_DIR"
  echo "====================================="
else
  echo "====================================="
  echo "Quá trình tạo đối thoại thất bại! Mã lỗi: $EXIT_CODE"
  echo "Thời gian kết thúc: $(date)"
  echo "Kiểm tra tệp nhật ký để biết chi tiết: logs/generate_${TIMESTAMP}.log"
  echo "====================================="
fi

# Count the number of generated dialogues
if [ -f "$OUTPUT_FILE" ]; then
  COUNT_ACTUAL=$(wc -l < "$OUTPUT_FILE")
  echo "Số lượng cuộc trò chuyện tạo ra: $COUNT_ACTUAL"
fi

exit $EXIT_CODE