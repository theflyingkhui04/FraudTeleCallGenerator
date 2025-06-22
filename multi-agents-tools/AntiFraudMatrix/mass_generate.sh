#!/bin/bash
# Script để chạy sinh dataset số lượng lớn
# Sử dụng: ./mass_generate.sh [API_KEY] [BASE_URL] [TOTAL_COUNT]

set -e

API_KEY=${1:-"sk-fpwiniyhjwughnzrzdckrrkiyxkebpgcoslhnenybgbxyvva"}
BASE_URL=${2:-"https://api.siliconflow.cn/v1"}
TOTAL_COUNT=${3:-1000}
MODEL=${4:-"deepseek-ai/DeepSeek-V2.5"}

echo "🚀 Bắt đầu sinh dataset số lượng lớn"
echo "   API: $BASE_URL"
echo "   Model: $MODEL"
echo "   Tổng số: $TOTAL_COUNT"

# Tạo thư mục kết quả
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="mass_dataset_$TIMESTAMP"
mkdir -p "$OUTPUT_DIR"

# Tính toán số lượng cho từng batch
BATCH_SIZE=100
FRAUD_RATIO=0.5
FRAUD_COUNT=$((TOTAL_COUNT * FRAUD_RATIO / 1))  # 50% fraud
NORMAL_COUNT=$((TOTAL_COUNT - FRAUD_COUNT))

echo "   Lừa đảo: $FRAUD_COUNT"
echo "   Bình thường: $NORMAL_COUNT"

# Chia thành các batch nhỏ để tránh timeout
FRAUD_BATCHES=$((FRAUD_COUNT / BATCH_SIZE + 1))
NORMAL_BATCHES=$((NORMAL_COUNT / BATCH_SIZE + 1))

echo "📦 Chia thành batches:"
echo "   Fraud batches: $FRAUD_BATCHES"
echo "   Normal batches: $NORMAL_BATCHES"

# Sinh fraud dialogues theo batch
echo "🚨 Sinh hội thoại lừa đảo..."
for ((i=1; i<=FRAUD_BATCHES; i++)); do
    START_IDX=$(((i-1) * BATCH_SIZE))
    END_IDX=$((i * BATCH_SIZE))
    if [ $END_IDX -gt $FRAUD_COUNT ]; then
        END_IDX=$FRAUD_COUNT
    fi
    CURRENT_BATCH_SIZE=$((END_IDX - START_IDX))
    
    if [ $CURRENT_BATCH_SIZE -gt 0 ]; then
        echo "   Batch $i/$FRAUD_BATCHES: $CURRENT_BATCH_SIZE dialogues"
        python optimized_generator.py \
            --fraud_count $CURRENT_BATCH_SIZE \
            --normal_count 0 \
            --api_key "$API_KEY" \
            --base_url "$BASE_URL" \
            --model "$MODEL" \
            --max_workers 2 \
            --delay 3 \
            --output_dir "$OUTPUT_DIR/fraud_batch_$i"
        
        # Nghỉ giữa các batch
        sleep 5
    fi
done

# Sinh normal dialogues theo batch
echo "📞 Sinh hội thoại bình thường..."
for ((i=1; i<=NORMAL_BATCHES; i++)); do
    START_IDX=$(((i-1) * BATCH_SIZE))
    END_IDX=$((i * BATCH_SIZE))
    if [ $END_IDX -gt $NORMAL_COUNT ]; then
        END_IDX=$NORMAL_COUNT
    fi
    CURRENT_BATCH_SIZE=$((END_IDX - START_IDX))
    
    if [ $CURRENT_BATCH_SIZE -gt 0 ]; then
        echo "   Batch $i/$NORMAL_BATCHES: $CURRENT_BATCH_SIZE dialogues"
        # Chạy script cho normal dialogues
        cd ../AntiFraudMatrix-normal
        python generate_normal_dialogues.py \
            --count $CURRENT_BATCH_SIZE \
            --api_key "$API_KEY" \
            --base_url "$BASE_URL" \
            --model "$MODEL" \
            --max_workers 2 \
            --delay 3 \
            --output "../AntiFraudMatrix/$OUTPUT_DIR/normal_batch_$i/normal_dialogues.jsonl" \
            --full_output_dir "../AntiFraudMatrix/$OUTPUT_DIR/normal_batch_$i/full_dialogues"
        cd ../AntiFraudMatrix
        
        # Nghỉ giữa các batch
        sleep 5
    fi
done

# Gộp tất cả các batch lại
echo "🔄 Gộp các batch..."
FINAL_FRAUD_FILE="$OUTPUT_DIR/all_fraud_dialogues.jsonl"
FINAL_NORMAL_FILE="$OUTPUT_DIR/all_normal_dialogues.jsonl"
FINAL_MERGED_FILE="$OUTPUT_DIR/final_merged_dataset.jsonl"

# Gộp fraud files
> "$FINAL_FRAUD_FILE"
for fraud_dir in "$OUTPUT_DIR"/fraud_batch_*; do
    if [ -d "$fraud_dir" ]; then
        cat "$fraud_dir"/*.jsonl >> "$FINAL_FRAUD_FILE" 2>/dev/null || true
    fi
done

# Gộp normal files
> "$FINAL_NORMAL_FILE"
for normal_dir in "$OUTPUT_DIR"/normal_batch_*; do
    if [ -d "$normal_dir" ]; then
        cat "$normal_dir"/*.jsonl >> "$FINAL_NORMAL_FILE" 2>/dev/null || true
    fi
done

# Gộp và thêm label
echo "🏷️ Thêm label và trộn dataset..."
python -c "
import json
import random

# Đọc fraud data
fraud_data = []
try:
    with open('$FINAL_FRAUD_FILE', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                data['label'] = 'fraud'
                data['is_fraud'] = 1
                fraud_data.append(data)
except:
    pass

# Đọc normal data  
normal_data = []
try:
    with open('$FINAL_NORMAL_FILE', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                data['label'] = 'normal'
                data['is_fraud'] = 0
                normal_data.append(data)
except:
    pass

# Gộp và trộn
all_data = fraud_data + normal_data
random.shuffle(all_data)

# Ghi ra file cuối
with open('$FINAL_MERGED_FILE', 'w', encoding='utf-8') as f:
    for item in all_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f'✅ Dataset hoàn thành:')
print(f'   - Fraud: {len(fraud_data)}')
print(f'   - Normal: {len(normal_data)}')
print(f'   - Tổng: {len(all_data)}')
print(f'   - File: $FINAL_MERGED_FILE')
"

# Tạo thống kê
echo "📊 Tạo thống kê dataset..."
python -c "
import json
from collections import defaultdict

stats = defaultdict(int)
fraud_types = defaultdict(int)
conv_types = defaultdict(int)
ages = defaultdict(int)
awareness = defaultdict(int)
occupations = defaultdict(int)

with open('$FINAL_MERGED_FILE', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            stats['total'] += 1
            stats[data.get('label', 'unknown')] += 1
            
            if data.get('fraud_type'):
                fraud_types[data['fraud_type']] += 1
            if data.get('conversation_type'):
                conv_types[data['conversation_type']] += 1
            if data.get('user_age'):
                age_group = f\"{data['user_age']//10*10}-{data['user_age']//10*10+9}\"
                ages[age_group] += 1
            if data.get('user_awareness'):
                awareness[data['user_awareness']] += 1
            if data.get('occupation'):
                occupations[data['occupation']] += 1

print('\\n📈 THỐNG KÊ DATASET:')
print(f'   Tổng: {stats[\"total\"]}')
print(f'   Fraud: {stats[\"fraud\"]} ({stats[\"fraud\"]/stats[\"total\"]*100:.1f}%)')
print(f'   Normal: {stats[\"normal\"]} ({stats[\"normal\"]/stats[\"total\"]*100:.1f}%)')
print(f'\\n🚨 Top fraud types:')
for ft, count in sorted(fraud_types.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f'   {ft}: {count}')
print(f'\\n📞 Top conversation types:')
for ct, count in sorted(conv_types.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f'   {ct}: {count}')
print(f'\\n👥 Age distribution:')
for age, count in sorted(ages.items()):
    print(f'   {age}: {count}')
print(f'\\n🧠 Awareness distribution:')
for aw, count in awareness.items():
    print(f'   {aw}: {count}')
"

echo ""
echo "🎉 Hoàn thành sinh dataset số lượng lớn!"
echo "📁 Kết quả tại: $OUTPUT_DIR"
echo "📄 File chính: $FINAL_MERGED_FILE"
echo ""
