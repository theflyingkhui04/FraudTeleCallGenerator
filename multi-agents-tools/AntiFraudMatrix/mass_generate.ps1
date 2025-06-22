# Script PowerShell để sinh dataset số lượng lớn trên Windows
param(
    [string]$ApiKey = "sk-fpwiniyhjwughnzrzdckrrkiyxkebpgcoslhnenybgbxyvva",
    [string]$BaseUrl = "https://api.siliconflow.cn/v1", 
    [int]$TotalCount = 1000,
    [string]$Model = "deepseek-ai/DeepSeek-V2.5"
)

Write-Host "🚀 Bắt đầu sinh dataset số lượng lớn" -ForegroundColor Green
Write-Host "   API: $BaseUrl"
Write-Host "   Model: $Model" 
Write-Host "   Tổng số: $TotalCount"

# Tạo thư mục kết quả
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputDir = "mass_dataset_$Timestamp"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# Tính toán số lượng
$BatchSize = 100
$FraudRatio = 0.5
$FraudCount = [math]::Floor($TotalCount * $FraudRatio)
$NormalCount = $TotalCount - $FraudCount

Write-Host "   Lừa đảo: $FraudCount" -ForegroundColor Yellow
Write-Host "   Bình thường: $NormalCount" -ForegroundColor Cyan

# Chia thành batches
$FraudBatches = [math]::Ceiling($FraudCount / $BatchSize)
$NormalBatches = [math]::Ceiling($NormalCount / $BatchSize)

Write-Host "📦 Chia thành batches:"
Write-Host "   Fraud batches: $FraudBatches"
Write-Host "   Normal batches: $NormalBatches"

# Function để chạy command với retry
function Invoke-WithRetry {
    param([scriptblock]$Command, [int]$MaxRetries = 3)
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            & $Command
            return
        }
        catch {
            Write-Warning "Attempt $i failed: $_"
            if ($i -eq $MaxRetries) { throw }
            Start-Sleep -Seconds (5 * $i)
        }
    }
}

# Sinh fraud dialogues
Write-Host "🚨 Sinh hội thoại lừa đảo..." -ForegroundColor Red
for ($i = 1; $i -le $FraudBatches; $i++) {
    $StartIdx = ($i - 1) * $BatchSize
    $EndIdx = $i * $BatchSize
    if ($EndIdx -gt $FraudCount) { $EndIdx = $FraudCount }
    $CurrentBatchSize = $EndIdx - $StartIdx
    
    if ($CurrentBatchSize -gt 0) {
        Write-Host "   Batch $i/$FraudBatches : $CurrentBatchSize dialogues" -ForegroundColor Yellow
        
        $BatchDir = "$OutputDir\fraud_batch_$i"
        New-Item -ItemType Directory -Path $BatchDir -Force | Out-Null
        
        Invoke-WithRetry {
            python batch_generate_dataset.py `
                --total_count $CurrentBatchSize `
                --fraud_ratio 1.0 `
                --api_key $ApiKey `
                --base_url $BaseUrl `
                --model $Model `
                --mode "fraud_only" `
                --output_dir $BatchDir
        }
        
        Start-Sleep -Seconds 3
    }
}

# Sinh normal dialogues
Write-Host "📞 Sinh hội thoại bình thường..." -ForegroundColor Blue
for ($i = 1; $i -le $NormalBatches; $i++) {
    $StartIdx = ($i - 1) * $BatchSize
    $EndIdx = $i * $BatchSize
    if ($EndIdx -gt $NormalCount) { $EndIdx = $NormalCount }
    $CurrentBatchSize = $EndIdx - $StartIdx
    
    if ($CurrentBatchSize -gt 0) {
        Write-Host "   Batch $i/$NormalBatches : $CurrentBatchSize dialogues" -ForegroundColor Cyan
        
        $BatchDir = "$OutputDir\normal_batch_$i"
        New-Item -ItemType Directory -Path $BatchDir -Force | Out-Null
        
        Invoke-WithRetry {
            python batch_generate_dataset.py `
                --total_count $CurrentBatchSize `
                --fraud_ratio 0.0 `
                --api_key $ApiKey `
                --base_url $BaseUrl `
                --model $Model `
                --mode "normal_only" `
                --output_dir $BatchDir
        }
        
        Start-Sleep -Seconds 3
    }
}

# Gộp các batch
Write-Host "🔄 Gộp các batch..." -ForegroundColor Magenta

$FinalFraudFile = "$OutputDir\all_fraud_dialogues.jsonl"
$FinalNormalFile = "$OutputDir\all_normal_dialogues.jsonl"
$FinalMergedFile = "$OutputDir\final_merged_dataset.jsonl"

# Gộp fraud files
New-Item -ItemType File -Path $FinalFraudFile -Force | Out-Null
Get-ChildItem "$OutputDir\fraud_batch_*\*.jsonl" -Recurse | ForEach-Object {
    Get-Content $_.FullName -Encoding UTF8 | Add-Content $FinalFraudFile -Encoding UTF8
}

# Gộp normal files
New-Item -ItemType File -Path $FinalNormalFile -Force | Out-Null
Get-ChildItem "$OutputDir\normal_batch_*\*.jsonl" -Recurse | ForEach-Object {
    Get-Content $_.FullName -Encoding UTF8 | Add-Content $FinalNormalFile -Encoding UTF8
}

# Gộp và thêm label
Write-Host "🏷️ Thêm label và trộn dataset..." -ForegroundColor Green

$MergeScript = @"
import json
import random
import sys

# Đọc fraud data
fraud_data = []
try:
    with open('$($FinalFraudFile.Replace('\', '/'))', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    data['label'] = 'fraud'
                    data['is_fraud'] = 1
                    fraud_data.append(data)
                except:
                    pass
except Exception as e:
    print(f'Error reading fraud file: {e}')

# Đọc normal data
normal_data = []
try:
    with open('$($FinalNormalFile.Replace('\', '/'))', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    data['label'] = 'normal'
                    data['is_fraud'] = 0
                    normal_data.append(data)
                except:
                    pass
except Exception as e:
    print(f'Error reading normal file: {e}')

# Gộp và trộn
all_data = fraud_data + normal_data
random.shuffle(all_data)

# Ghi ra file cuối
with open('$($FinalMergedFile.Replace('\', '/'))', 'w', encoding='utf-8') as f:
    for item in all_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f'✅ Dataset hoàn thành:')
print(f'   - Fraud: {len(fraud_data)}')
print(f'   - Normal: {len(normal_data)}')
print(f'   - Tổng: {len(all_data)}')
print(f'   - File: $($FinalMergedFile.Replace('\', '/'))')
"@

$MergeScript | python

# Tạo thống kê
Write-Host "📊 Tạo thống kê dataset..." -ForegroundColor Cyan

$StatsScript = @"
import json
from collections import defaultdict

stats = defaultdict(int)
fraud_types = defaultdict(int)
conv_types = defaultdict(int)
ages = defaultdict(int)
awareness = defaultdict(int)
occupations = defaultdict(int)

try:
    with open('$($FinalMergedFile.Replace('\', '/'))', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    stats['total'] += 1
                    stats[data.get('label', 'unknown')] += 1
                    
                    if data.get('fraud_type'):
                        fraud_types[data['fraud_type']] += 1
                    if data.get('conversation_type'):
                        conv_types[data['conversation_type']] += 1
                    if data.get('user_age'):
                        age_group = f"{data['user_age']//10*10}-{data['user_age']//10*10+9}"
                        ages[age_group] += 1
                    if data.get('user_awareness'):
                        awareness[data['user_awareness']] += 1
                    if data.get('occupation'):
                        occupations[data['occupation']] += 1
                except:
                    pass
except Exception as e:
    print(f'Error reading merged file: {e}')

print('\n📈 THỐNG KÊ DATASET:')
print(f'   Tổng: {stats["total"]}')
if stats["total"] > 0:
    print(f'   Fraud: {stats["fraud"]} ({stats["fraud"]/stats["total"]*100:.1f}%)')
    print(f'   Normal: {stats["normal"]} ({stats["normal"]/stats["total"]*100:.1f}%)')

if fraud_types:
    print(f'\n🚨 Top fraud types:')
    for ft, count in sorted(fraud_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f'   {ft}: {count}')

if conv_types:
    print(f'\n📞 Top conversation types:')
    for ct, count in sorted(conv_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f'   {ct}: {count}')

if ages:
    print(f'\n👥 Age distribution:')
    for age, count in sorted(ages.items()):
        print(f'   {age}: {count}')

if awareness:
    print(f'\n🧠 Awareness distribution:')
    for aw, count in awareness.items():
        print(f'   {aw}: {count}')
"@

$StatsScript | python

Write-Host ""
Write-Host "🎉 Hoàn thành sinh dataset số lượng lớn!" -ForegroundColor Green
Write-Host "📁 Kết quả tại: $OutputDir" -ForegroundColor Yellow
Write-Host "📄 File chính: $FinalMergedFile" -ForegroundColor Yellow
Write-Host ""
