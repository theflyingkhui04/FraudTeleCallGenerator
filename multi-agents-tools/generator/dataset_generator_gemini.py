#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sinh dataset hội thoại với Gemini API
"""

import os
import json
import sys
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Sinh dataset hội thoại lừa đảo và bình thường với Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Sinh 100 hội thoại cân bằng (50% lừa đảo, 50% bình thường)
  python dataset_generator_gemini.py --total 100 --api_key YOUR_GEMINI_KEY --model gemini-2.0-flash

  # Chỉ sinh hội thoại lừa đảo
  python dataset_generator_gemini.py --fraud_only 50 --api_key YOUR_GEMINI_KEY

  # Chỉ sinh hội thoại bình thường
  python dataset_generator_gemini.py --normal_only 30 --api_key YOUR_GEMINI_KEY
        """
    )
    
    # Nhóm tham số chính
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--total", type=int, help="Tổng số hội thoại cần sinh (sẽ cân bằng 50-50)")
    group.add_argument("--fraud_only", type=int, help="Chỉ sinh hội thoại lừa đảo")
    group.add_argument("--normal_only", type=int, help="Chỉ sinh hội thoại bình thường")
    
    # Tham số API
    parser.add_argument("--api_key", required=True, help="Gemini API key (bắt buộc)")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Model Gemini")
    parser.add_argument("--fraud_ratio", type=float, default=0.5, help="Tỷ lệ hội thoại lừa đảo (0.0-1.0)")
    
    args = parser.parse_args()
    
    # Kiểm tra tham số
    if args.fraud_ratio < 0 or args.fraud_ratio > 1:
        parser.error("fraud_ratio phải trong khoảng 0.0-1.0")
    
    # Tạo thư mục output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_dir = Path(__file__).parent
    dataset_dir = current_dir / "dataset"
    dataset_dir.mkdir(exist_ok=True)
    
    print(f"🚀 Bắt đầu sinh dataset với Gemini API")
    print(f"   - Model: {args.model}")
    print(f"   - Dataset dir: {dataset_dir}")
    
    # Tính toán số lượng
    if args.total:
        fraud_count = int(args.total * args.fraud_ratio)
        normal_count = args.total - fraud_count
        print(f"   - Tổng: {args.total} (Lừa đảo: {fraud_count}, Bình thường: {normal_count})")
    elif args.fraud_only:
        fraud_count = args.fraud_only
        normal_count = 0
        print(f"   - Chỉ lừa đảo: {fraud_count}")
    else:  # args.normal_only
        fraud_count = 0
        normal_count = args.normal_only
        print(f"   - Chỉ bình thường: {normal_count}")
    
    results = {}
    
    # Sinh hội thoại lừa đảo
    if fraud_count > 0:
        print(f"\n🚨 Sinh {fraud_count} hội thoại lừa đảo...")
        fraud_dir = dataset_dir / f"fraud_{timestamp}"
        fraud_dir.mkdir(exist_ok=True)
        
        # Script path
        script_path = current_dir.parent / "AntiFraudMatrix" / "generate_dialogues.py"
        
        cmd = [
            sys.executable, str(script_path),
            "--count", str(fraud_count),
            "--output", str(fraud_dir / "fraud_conversations.jsonl"),
            "--api_key", args.api_key,
            "--model", args.model,
            "--workers", "2"
        ]
        
        try:
            print(f"   Chạy: {' '.join(cmd[:3])} [với API params]")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print(f"   ✅ Hoàn thành sinh hội thoại lừa đảo")
                results["fraud"] = {"count": fraud_count, "status": "success"}
            else:
                print(f"   ❌ Lỗi: {result.stderr}")
                results["fraud"] = {"count": fraud_count, "status": "failed", "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout sau 1 giờ")
            results["fraud"] = {"count": fraud_count, "status": "timeout"}
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results["fraud"] = {"count": fraud_count, "status": "exception", "error": str(e)}
    
    # Sinh hội thoại bình thường
    if normal_count > 0:
        print(f"\n💬 Sinh {normal_count} hội thoại bình thường...")
        normal_dir = dataset_dir / f"normal_{timestamp}"
        normal_dir.mkdir(exist_ok=True)
        
        # Script path
        script_path = current_dir.parent / "AntiFraudMatrix-normal" / "generate_normal_dialogues.py"
        
        cmd = [
            sys.executable, str(script_path),
            "--count", str(normal_count),
            "--output", str(normal_dir / "normal_conversations.jsonl"),
            "--api_key", args.api_key,
            "--model", args.model,
            "--workers", "2"
        ]
        
        try:
            print(f"   Chạy: {' '.join(cmd[:3])} [với API params]")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print(f"   ✅ Hoàn thành sinh hội thoại bình thường")
                results["normal"] = {"count": normal_count, "status": "success"}
            else:
                print(f"   ❌ Lỗi: {result.stderr}")
                results["normal"] = {"count": normal_count, "status": "failed", "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout sau 1 giờ")
            results["normal"] = {"count": normal_count, "status": "timeout"}
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results["normal"] = {"count": normal_count, "status": "exception", "error": str(e)}
    
    # Tổng kết
    print(f"\n📊 Tổng kết:")
    for category, info in results.items():
        print(f"   - {category.capitalize()}: {info['count']} hội thoại - {info['status']}")
    
    # Lưu kết quả tổng kết
    summary_file = dataset_dir / f"generation_results_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Kết quả lưu trong: {dataset_dir}")
    print(f"📄 Tổng kết: {summary_file}")

if __name__ == "__main__":
    main()
