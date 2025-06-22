#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sinh số lượng lớn hội thoại lừa đảo và không lừa đảo
Tự động tạo dataset cân bằng với đa dạng tham số
"""

import os
import json
import random
import argparse
import time
import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Import từ dự án hiện tại
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

class DatasetGenerator:
    """Class chính để sinh dataset lớn"""
    
    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-ai/DeepSeek-V2.5"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Cấu hình logging
        log_file = f"dataset_generation_{self.timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_fraud_dialogues(self, count: int, output_dir: str = "fraud_dataset") -> Dict[str, Any]:
        """Sinh hội thoại lừa đảo"""
        self.logger.info(f"🚨 Bắt đầu sinh {count} hội thoại lừa đảo...")
        
        # Tạo thư mục output
        os.makedirs(output_dir, exist_ok=True)
        full_output_dir = os.path.join(output_dir, "full_dialogues")
        os.makedirs(full_output_dir, exist_ok=True)
          # Tệp kết quả
        output_file = os.path.join(output_dir, f"fraud_dialogues_{self.timestamp}.jsonl")
        
        # Chạy script sinh hội thoại lừa đảo
        cmd = [
            sys.executable, "generate_dialogues.py",
            "--count", str(count),
            "--output", output_file,
            "--full_output_dir", full_output_dir,
            "--api_key", self.api_key,
            "--base_url", self.base_url,
            "--model", self.model,
            "--workers", "3",  # Sử dụng --workers thay vì --max_workers
            "--max_turns", "25"  # Thêm max_turns để có hội thoại dài hơn
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".", encoding='utf-8')
            if result.returncode == 0:
                self.logger.info(f"✅ Sinh hội thoại lừa đảo thành công: {output_file}")
                return {"status": "success", "output_file": output_file, "full_dir": full_output_dir}
            else:
                self.logger.error(f"❌ Lỗi sinh hội thoại lừa đảo: {result.stderr}")
                return {"status": "error", "error": result.stderr}
        except Exception as e:
            self.logger.error(f"❌ Exception khi sinh hội thoại lừa đảo: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_normal_dialogues(self, count: int, output_dir: str = "normal_dataset") -> Dict[str, Any]:
        """Sinh hội thoại bình thường"""
        self.logger.info(f"📞 Bắt đầu sinh {count} hội thoại bình thường...")
        
        # Tạo thư mục output
        os.makedirs(output_dir, exist_ok=True)
        full_output_dir = os.path.join(output_dir, "full_dialogues")
        os.makedirs(full_output_dir, exist_ok=True)
          # Tệp kết quả
        output_file = os.path.join(output_dir, f"normal_dialogues_{self.timestamp}.jsonl")
        
        # Chạy script sinh hội thoại bình thường
        normal_script_path = "../AntiFraudMatrix-normal/generate_normal_dialogues.py"
        cmd = [
            sys.executable, normal_script_path,
            "--count", str(count),
            "--output", output_file,
            "--full_output_dir", full_output_dir,
            "--api_key", self.api_key,
            "--base_url", self.base_url,
            "--model", self.model,
            "--workers", "3",  # Sử dụng --workers thay vì --max_workers
            "--max_turns", "20"  # Thêm max_turns
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".", encoding='utf-8')            if result.returncode == 0:
                self.logger.info(f"✅ Sinh hội thoại bình thường thành công: {output_file}")
                return {"status": "success", "output_file": output_file, "full_dir": full_output_dir}
            else:
                self.logger.error(f"❌ Lỗi sinh hội thoại bình thường: {result.stderr}")
                return {"status": "error", "error": result.stderr}
        except Exception as e:
            self.logger.error(f"❌ Exception khi sinh hội thoại bình thường: {e}")
            return {"status": "error", "error": str(e)}
    
    def merge_datasets(self, fraud_file: str, normal_file: str, output_file: str = None) -> str:
        """Gộp hai dataset và thêm nhãn"""
        if output_file is None:
            output_file = f"merged_dataset_{self.timestamp}.jsonl"
        
        self.logger.info(f"🔄 Gộp dataset: {fraud_file} + {normal_file} -> {output_file}")
        
        merged_data = []
        
        # Đọc hội thoại lừa đảo
        if os.path.exists(fraud_file):
            with open(fraud_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    data['label'] = 'fraud'  # Thêm nhãn
                    data['is_fraud'] = 1
                    merged_data.append(data)
        
        # Đọc hội thoại bình thường
        if os.path.exists(normal_file):
            with open(normal_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    data['label'] = 'normal'  # Thêm nhãn
                    data['is_fraud'] = 0
                    merged_data.append(data)
        
        # Trộn ngẫu nhiên
        random.shuffle(merged_data)
        
        # Ghi ra file
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in merged_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        self.logger.info(f"✅ Đã gộp {len(merged_data)} hội thoại vào {output_file}")
        return output_file
    
    def generate_balanced_dataset(self, total_count: int, fraud_ratio: float = 0.5, 
                                 output_dir: str = None) -> Dict[str, Any]:
        """Sinh dataset cân bằng với tỷ lệ lừa đảo/bình thường"""
        if output_dir is None:
            output_dir = f"balanced_dataset_{self.timestamp}"
        
        fraud_count = int(total_count * fraud_ratio)
        normal_count = total_count - fraud_count
        
        self.logger.info(f"🎯 Sinh dataset cân bằng:")
        self.logger.info(f"   - Tổng: {total_count} hội thoại")
        self.logger.info(f"   - Lừa đảo: {fraud_count} ({fraud_ratio*100:.1f}%)")
        self.logger.info(f"   - Bình thường: {normal_count} ({(1-fraud_ratio)*100:.1f}%)")
        
        # Tạo thư mục chính
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        # Sinh hội thoại lừa đảo
        if fraud_count > 0:
            fraud_dir = os.path.join(output_dir, "fraud")
            fraud_result = self.generate_fraud_dialogues(fraud_count, fraud_dir)
            results['fraud'] = fraud_result
        
        # Sinh hội thoại bình thường
        if normal_count > 0:
            normal_dir = os.path.join(output_dir, "normal")
            normal_result = self.generate_normal_dialogues(normal_count, normal_dir)
            results['normal'] = normal_result
        
        # Gộp dataset nếu cả hai đều thành công
        if (results.get('fraud', {}).get('status') == 'success' and 
            results.get('normal', {}).get('status') == 'success'):
            
            fraud_file = results['fraud']['output_file']
            normal_file = results['normal']['output_file']
            merged_file = os.path.join(output_dir, f"merged_dataset_{self.timestamp}.jsonl")
            
            final_dataset = self.merge_datasets(fraud_file, normal_file, merged_file)
            results['merged'] = {"status": "success", "output_file": final_dataset}
            
            # Tạo thống kê
            self.create_dataset_stats(final_dataset, output_dir)
        
        return results
    
    def create_dataset_stats(self, dataset_file: str, output_dir: str):
        """Tạo thống kê dataset"""
        stats = {
            "total_dialogues": 0,
            "fraud_count": 0,
            "normal_count": 0,
            "fraud_types": {},
            "conversation_types": {},
            "age_distribution": {},
            "awareness_distribution": {},
            "occupation_distribution": {}
        }
        
        with open(dataset_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                stats["total_dialogues"] += 1
                
                if data.get('is_fraud', 0) == 1:
                    stats["fraud_count"] += 1
                    fraud_type = data.get('fraud_type', 'unknown')
                    stats["fraud_types"][fraud_type] = stats["fraud_types"].get(fraud_type, 0) + 1
                else:
                    stats["normal_count"] += 1
                    conv_type = data.get('conversation_type', 'unknown')
                    stats["conversation_types"][conv_type] = stats["conversation_types"].get(conv_type, 0) + 1
                
                # Thống kê chung
                age = data.get('user_age', 'unknown')
                awareness = data.get('user_awareness', 'unknown')
                occupation = data.get('occupation', 'unknown')
                
                stats["age_distribution"][str(age)] = stats["age_distribution"].get(str(age), 0) + 1
                stats["awareness_distribution"][awareness] = stats["awareness_distribution"].get(awareness, 0) + 1
                stats["occupation_distribution"][occupation] = stats["occupation_distribution"].get(occupation, 0) + 1
        
        # Ghi thống kê
        stats_file = os.path.join(output_dir, f"dataset_stats_{self.timestamp}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # In thống kê
        self.logger.info(f"📊 THỐNG KÊ DATASET:")
        self.logger.info(f"   - Tổng hội thoại: {stats['total_dialogues']}")
        self.logger.info(f"   - Lừa đảo: {stats['fraud_count']} ({stats['fraud_count']/stats['total_dialogues']*100:.1f}%)")
        self.logger.info(f"   - Bình thường: {stats['normal_count']} ({stats['normal_count']/stats['total_dialogues']*100:.1f}%)")
        self.logger.info(f"   - Chi tiết lưu tại: {stats_file}")

def main():
    parser = argparse.ArgumentParser(description="Sinh số lượng lớn dataset hội thoại lừa đảo và bình thường")
    parser.add_argument("--total_count", type=int, default=1000, help="Tổng số hội thoại cần sinh")
    parser.add_argument("--fraud_ratio", type=float, default=0.5, help="Tỷ lệ hội thoại lừa đảo (0.0-1.0)")
    parser.add_argument("--api_key", required=True, help="API key")
    parser.add_argument("--base_url", required=True, help="Base URL API")
    parser.add_argument("--model", default="deepseek-ai/DeepSeek-V2.5", help="Model AI")
    parser.add_argument("--output_dir", help="Thư mục output (mặc định: balanced_dataset_timestamp)")
    parser.add_argument("--mode", choices=["balanced", "fraud_only", "normal_only"], 
                       default="balanced", help="Chế độ sinh dataset")
    
    args = parser.parse_args()
    
    # Tạo generator
    generator = DatasetGenerator(args.api_key, args.base_url, args.model)
    
    start_time = time.time()
    
    try:
        if args.mode == "balanced":
            results = generator.generate_balanced_dataset(
                args.total_count, args.fraud_ratio, args.output_dir
            )
        elif args.mode == "fraud_only":
            results = generator.generate_fraud_dialogues(args.total_count, args.output_dir or "fraud_only_dataset")
        elif args.mode == "normal_only":
            results = generator.generate_normal_dialogues(args.total_count, args.output_dir or "normal_only_dataset")
        
        elapsed = time.time() - start_time
        generator.logger.info(f"🏁 Hoàn thành trong {elapsed:.2f} giây")
        generator.logger.info(f"📋 Kết quả: {json.dumps(results, ensure_ascii=False, indent=2)}")
        
    except KeyboardInterrupt:
        generator.logger.info("❌ Bị hủy bởi người dùng")
    except Exception as e:
        generator.logger.error(f"❌ Lỗi nghiêm trọng: {e}", exc_info=True)

if __name__ == "__main__":
    main()
