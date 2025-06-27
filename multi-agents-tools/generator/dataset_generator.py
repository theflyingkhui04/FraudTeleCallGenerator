#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sinh dataset hội thoại lừa đảo và bình thường
Tích hợp cả hai loại hội thoại vào một dataset cân bằng
"""

import os
import json
import sys
import argparse
import logging
import subprocess
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class DatasetGenerator:
    """Class sinh dataset hội thoại lừa đảo và bình thường"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.base_url = base_url or ""  # Empty string for Gemini
        self.model = model
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Đường dẫn các thư mục
        self.current_dir = Path(__file__).parent
        self.project_root = self.current_dir.parent
        self.dataset_dir = self.project_root / "dataset"
        self.fraud_script = self.project_root / "AntiFraudMatrix" / "generate_dialogues.py"
        self.normal_script = self.project_root / "AntiFraudMatrix-normal" / "generate_normal_dialogues.py"
        
        # Tạo thư mục dataset
        self.dataset_dir.mkdir(exist_ok=True)
          # Cấu hình logging với encoding an toàn cho Windows
        log_file = self.dataset_dir / f"generator_log_{self.timestamp}.log"
        
        # Tạo formatter với encoding UTF-8
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler với UTF-8
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Stream handler với UTF-8 (Windows safe)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
          # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, stream_handler],
            force=True
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🚀 Khởi tạo Dataset Generator")
        self.logger.info(f"   - API: {base_url or 'Gemini (built-in)'}")
        self.logger.info(f"   - Model: {model}")
        self.logger.info(f"   - Dataset dir: {self.dataset_dir}")
    
    def generate_fraud_conversations(self, count: int) -> Dict[str, Any]:
        """Sinh hội thoại lừa đảo"""
        self.logger.info(f"🚨 Sinh {count} hội thoại lừa đảo...")
        
        # Tạo thư mục output
        fraud_dir = self.dataset_dir / f"fraud_{self.timestamp}"
        fraud_dir.mkdir(exist_ok=True)
        full_dir = fraud_dir / "full_dialogues"
        full_dir.mkdir(exist_ok=True)
        
        output_file = fraud_dir / "fraud_conversations.jsonl"        # Command để chạy script lừa đảo
        cmd = [
            sys.executable, str(self.fraud_script),
            "--count", str(count),
            "--output", str(output_file),
            "--full_output_dir", str(full_dir),
            "--api_key", self.api_key,
            "--model", self.model,
            "--workers", "3",
            "--max_turns", "25"
        ]
        # Chỉ thêm base_url nếu được cung cấp (không phải Gemini)
        if self.base_url:
            cmd.extend(["--base_url", self.base_url])
        
        try:
            self.logger.info(f"   Chạy lệnh: {' '.join(cmd[:3])} [với API params]")
            
            # Set environment for UTF-8 encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Sử dụng Popen để stream output real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.fraud_script.parent),
                encoding='utf-8',
                errors='replace',
                env=env,
                bufsize=1,
                universal_newlines=True
            )
              # Stream output real-time
            stdout_lines = []
            if process.stdout:
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        # In ra terminal và lưu vào log
                        line = output.strip()
                        stdout_lines.append(line)
                        # Thêm prefix để phân biệt
                        print(f"[FRAUD] {line}")
            
            return_code = process.poll()
            
            if return_code == 0:
                self.logger.info(f"✅ Sinh hội thoại lừa đảo thành công")
                return {
                    "status": "success",
                    "count": count,
                    "output_file": str(output_file),
                    "full_dir": str(full_dir)
                }
            else:
                self.logger.error(f"❌ Lỗi sinh hội thoại lừa đảo (exit code: {return_code})")
                return {
                    "status": "error", 
                    "error": f"Process exited with code {return_code}",
                    "stdout": stdout_lines
                }
                
        except Exception as e:
            self.logger.error(f"❌ Exception sinh hội thoại lừa đảo: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_normal_conversations(self, count: int) -> Dict[str, Any]:
        """Sinh hội thoại bình thường"""
        self.logger.info(f"📞 Sinh {count} hội thoại bình thường...")
        
        # Tạo thư mục output
        normal_dir = self.dataset_dir / f"normal_{self.timestamp}"
        normal_dir.mkdir(exist_ok=True)
        full_dir = normal_dir / "full_dialogues"
        full_dir.mkdir(exist_ok=True)
        
        output_file = normal_dir / "normal_conversations.jsonl"
        # Command để chạy script bình thường
        cmd = [
            sys.executable, str(self.normal_script),
            "--count", str(count),
            "--output", str(output_file),
            "--full_output_dir", str(full_dir),
            "--api_key", self.api_key,
            "--model", self.model,
            "--workers", "3",
            "--max_turns", "20"
        ]
        # Chỉ thêm base_url nếu được cung cấp (không phải Gemini)
        if self.base_url:
            cmd.extend(["--base_url", self.base_url])
        
        try:
            self.logger.info(f"   Chạy lệnh: {' '.join(cmd[:3])} [với API params]")
            
            # Set environment for UTF-8 encoding
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Sử dụng Popen để stream output real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.normal_script.parent),
                encoding='utf-8',
                errors='replace',
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output real-time
            stdout_lines = []
            if process.stdout:
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        # In ra terminal và lưu vào log
                        line = output.strip()
                        stdout_lines.append(line)
                        # Thêm prefix để phân biệt
                        print(f"[NORMAL] {line}")
            
            return_code = process.poll()
            
            if return_code == 0:
                self.logger.info(f"✅ Sinh hội thoại bình thường thành công")
                return {
                    "status": "success",
                    "count": count,
                    "output_file": str(output_file),
                    "full_dir": str(full_dir)
                }
            else:
                self.logger.error(f"❌ Lỗi sinh hội thoại bình thường (exit code: {return_code})")
                return {
                    "status": "error", 
                    "error": f"Process exited with code {return_code}",
                    "stdout": stdout_lines                }
                
        except Exception as e:
            self.logger.error(f"❌ Exception sinh hội thoại bình thường: {e}")
            return {"status": "error", "error": str(e)}
    
    def merge_and_balance_dataset(self, fraud_file: str, normal_file: str, 
                                 output_name: Optional[str] = None) -> Dict[str, Any]:
        """Gộp và cân bằng dataset"""
        if output_name is None:
            output_name = f"balanced_dataset_{self.timestamp}"
        
        output_dir = self.dataset_dir / output_name
        output_dir.mkdir(exist_ok=True)
        
        merged_file = output_dir / "merged_conversations.jsonl"
        
        self.logger.info(f"🔄 Gộp và cân bằng dataset...")
        
        conversations = []
        
        # Đọc hội thoại lừa đảo
        fraud_count = 0
        if os.path.exists(fraud_file):
            with open(fraud_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        data['label'] = 'fraud'
                        data['is_fraud'] = 1
                        conversations.append(data)
                        fraud_count += 1
        
        # Đọc hội thoại bình thường
        normal_count = 0
        if os.path.exists(normal_file):
            with open(normal_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        data['label'] = 'normal'
                        data['is_fraud'] = 0
                        conversations.append(data)
                        normal_count += 1
        
        # Trộn ngẫu nhiên
        random.shuffle(conversations)
        
        # Ghi file gộp
        with open(merged_file, 'w', encoding='utf-8') as f:
            for conv in conversations:
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        # Tạo thống kê
        stats = self.create_dataset_statistics(conversations, output_dir)
        
        result = {
            "status": "success",
            "total_conversations": len(conversations),
            "fraud_count": fraud_count,
            "normal_count": normal_count,
            "fraud_ratio": fraud_count / len(conversations) if conversations else 0,
            "output_file": str(merged_file),
            "output_dir": str(output_dir),
            "stats_file": str(output_dir / "statistics.json")
        }
        
        self.logger.info(f"✅ Gộp dataset thành công:")
        self.logger.info(f"   - Tổng: {len(conversations)} hội thoại")
        self.logger.info(f"   - Lừa đảo: {fraud_count} ({fraud_count/len(conversations)*100:.1f}%)")
        self.logger.info(f"   - Bình thường: {normal_count} ({normal_count/len(conversations)*100:.1f}%)")
        self.logger.info(f"   - File: {merged_file}")
        
        return result
    
    def create_dataset_statistics(self, conversations: List[Dict], output_dir: Path) -> Dict[str, Any]:
        """Tạo thống kê chi tiết dataset"""
        stats = {
            "generation_info": {
                "timestamp": self.timestamp,
                "total_conversations": len(conversations),
                "model": self.model,
                "api_base": self.base_url
            },
            "label_distribution": {"fraud": 0, "normal": 0},
            "fraud_types": {},
            "conversation_types": {},
            "user_demographics": {
                "age_groups": {},
                "occupations": {},
                "awareness_levels": {}
            },
            "conversation_quality": {
                "avg_turns": 0,
                "turn_distribution": {},
                "avg_length": 0
            }
        }
        
        total_turns = 0
        total_length = 0
        
        for conv in conversations:
            # Phân loại cơ bản
            label = conv.get('label', 'unknown')
            stats["label_distribution"][label] = stats["label_distribution"].get(label, 0) + 1
            
            # Loại lừa đảo
            if label == 'fraud':
                fraud_type = conv.get('fraud_type', 'unknown')
                stats["fraud_types"][fraud_type] = stats["fraud_types"].get(fraud_type, 0) + 1
            
            # Loại hội thoại bình thường
            if label == 'normal':
                conv_type = conv.get('conversation_type', 'unknown')
                stats["conversation_types"][conv_type] = stats["conversation_types"].get(conv_type, 0) + 1
            
            # Thông tin người dùng
            age = str(conv.get('user_age', 'unknown'))
            occupation = conv.get('occupation', 'unknown')
            awareness = conv.get('user_awareness', 'unknown')
            
            stats["user_demographics"]["age_groups"][age] = stats["user_demographics"]["age_groups"].get(age, 0) + 1
            stats["user_demographics"]["occupations"][occupation] = stats["user_demographics"]["occupations"].get(occupation, 0) + 1
            stats["user_demographics"]["awareness_levels"][awareness] = stats["user_demographics"]["awareness_levels"].get(awareness, 0) + 1
            
            # Chất lượng hội thoại
            dialogue = conv.get('dialogue', [])
            turns = len(dialogue)
            total_turns += turns
            
            turn_range = f"{(turns//5)*5}-{(turns//5)*5+4}"
            stats["conversation_quality"]["turn_distribution"][turn_range] = stats["conversation_quality"]["turn_distribution"].get(turn_range, 0) + 1
            
            # Độ dài text
            text_length = sum(len(turn.get('content', '')) for turn in dialogue)
            total_length += text_length
        
        # Tính trung bình
        if conversations:
            stats["conversation_quality"]["avg_turns"] = total_turns / len(conversations)
            stats["conversation_quality"]["avg_length"] = total_length / len(conversations)
        
        # Ghi file thống kê
        stats_file = output_dir / "statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return stats
    
    def generate_balanced_dataset(self, total_count: int, fraud_ratio: float = 0.5) -> Dict[str, Any]:
        """Sinh dataset cân bằng với tỷ lệ lừa đảo/bình thường tùy chỉnh"""
        fraud_count = int(total_count * fraud_ratio)
        normal_count = total_count - fraud_count
        
        self.logger.info(f"🎯 Sinh dataset cân bằng:")
        self.logger.info(f"   - Tổng: {total_count} hội thoại")
        self.logger.info(f"   - Lừa đảo: {fraud_count} ({fraud_ratio*100:.1f}%)")
        self.logger.info(f"   - Bình thường: {normal_count} ({(1-fraud_ratio)*100:.1f}%)")
        
        results = {}
        
        # Sinh hội thoại lừa đảo
        if fraud_count > 0:
            fraud_result = self.generate_fraud_conversations(fraud_count)
            results['fraud'] = fraud_result
        
        # Sinh hội thoại bình thường
        if normal_count > 0:
            normal_result = self.generate_normal_conversations(normal_count)
            results['normal'] = normal_result
        
        # Gộp dataset nếu cả hai thành công
        if (results.get('fraud', {}).get('status') == 'success' and 
            results.get('normal', {}).get('status') == 'success'):
            
            merge_result = self.merge_and_balance_dataset(
                results['fraud']['output_file'],
                results['normal']['output_file']
            )
            results['merged'] = merge_result
        
        return results

def main():
    parser = argparse.ArgumentParser(
        description="Sinh dataset hội thoại lừa đảo và bình thường",
        formatter_class=argparse.RawDescriptionHelpFormatter,        epilog="""
Ví dụ sử dụng:
  # Sinh 1000 hội thoại cân bằng (50% lừa đảo, 50% bình thường)
  python dataset_generator.py --total 1000 --api_key YOUR_GEMINI_KEY --model gemini-2.0-flash

  # Sinh 500 hội thoại với 70% lừa đảo
  python dataset_generator.py --total 500 --fraud_ratio 0.7 --api_key YOUR_GEMINI_KEY --model gemini-2.0-flash

  # Chỉ sinh hội thoại lừa đảo
  python dataset_generator.py --fraud_only 300 --api_key YOUR_GEMINI_KEY --model gemini-2.0-flash

  # Chỉ sinh hội thoại bình thường
  python dataset_generator.py --normal_only 200 --api_key YOUR_GEMINI_KEY --model gemini-2.0-flash
        """
    )
    
    # Nhóm tham số chính
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--total", type=int, help="Tổng số hội thoại cần sinh (sẽ cân bằng theo fraud_ratio)")
    group.add_argument("--fraud_only", type=int, help="Chỉ sinh hội thoại lừa đảo")
    group.add_argument("--normal_only", type=int, help="Chỉ sinh hội thoại bình thường")
      # Tham số API
    parser.add_argument("--api_key", required=True, help="API key (bắt buộc)")
    parser.add_argument("--base_url", help="Base URL API (không cần cho Gemini)")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Model AI")
    # Tham số tùy chỉnh
    parser.add_argument("--fraud_ratio", type=float, default=0.5, 
                       help="Ty le hoi thoai lua dao (0.0-1.0, mac dinh 0.5)")
    
    args = parser.parse_args()
    
    # Kiểm tra tham số
    if args.fraud_ratio < 0 or args.fraud_ratio > 1:
        parser.error("fraud_ratio phải trong khoảng 0.0-1.0")
      # Tạo generator
    generator = DatasetGenerator(args.api_key, args.base_url, args.model)
    
    start_time = time.time()
    results = {}
    
    try:
        if args.total:
            # Sinh dataset cân bằng
            results = generator.generate_balanced_dataset(args.total, args.fraud_ratio)
            
        elif args.fraud_only:
            # Chỉ sinh lừa đảo
            results = {"fraud": generator.generate_fraud_conversations(args.fraud_only)}
            
        elif args.normal_only:
            # Chỉ sinh bình thường
            results = {"normal": generator.generate_normal_conversations(args.normal_only)}
        
        elapsed = time.time() - start_time
        generator.logger.info(f"🏁 Hoàn thành trong {elapsed:.2f} giây")
        
        # In kết quả tóm tắt
        generator.logger.info("📋 KẾT QUẢ TỔNG QUAN:")
        for key, result in results.items():
            if result.get('status') == 'success':
                generator.logger.info(f"   ✅ {key}: {result.get('count', '?')} hội thoại")
            else:
                generator.logger.info(f"   ❌ {key}: {result.get('error', 'Lỗi không xác định')}")
        
        # Ghi kết quả chi tiết
        result_file = generator.dataset_dir / f"generation_results_{generator.timestamp}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        generator.logger.info(f"📄 Chi tiết kết quả: {result_file}")
        
    except KeyboardInterrupt:
        generator.logger.info("❌ Bị hủy bởi người dùng")
        sys.exit(1)
    except Exception as e:
        generator.logger.error(f"❌ Lỗi nghiêm trọng: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
