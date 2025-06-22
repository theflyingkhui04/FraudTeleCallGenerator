#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sinh dataset nhanh với các cấu hình có sẵn
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Chạy lệnh với mô tả"""
    print(f"\n🚀 {description}")
    print(f"📝 Lệnh: {' '.join(cmd[:5])} ...")
    
    try:
        result = subprocess.run(cmd, check=True, text=True, encoding='utf-8')
        print(f"✅ Thành công!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi: {e}")
        return False

def main():
    # Cấu hình API (cần điều chỉnh theo API của bạn)
    API_KEY = "sk-snqprjadkwbxggowrmzmzkdhsdajpdlqirgeopejlalyvbxb"
    BASE_URL = "https://api.siliconflow.cn/v1"
    MODEL = "deepseek-ai/DeepSeek-V2.5"
    
    generator_script = Path(__file__).parent / "dataset_generator.py"
    
    print("🎯 Dataset Generator - Preset Configurations")
    print("=" * 50)
    
    # Các cấu hình có sẵn
    configs = [
        {
            "name": "Dataset nhỏ (100 hội thoại, 50-50)",
            "cmd": [sys.executable, str(generator_script), 
                   "--total", "100", 
                   "--api_key", API_KEY, 
                   "--base_url", BASE_URL, 
                   "--model", MODEL]
        },
        {
            "name": "Dataset trung bình (500 hội thoại, 60% lừa đảo)",
            "cmd": [sys.executable, str(generator_script), 
                   "--total", "500", 
                   "--fraud_ratio", "0.6",
                   "--api_key", API_KEY, 
                   "--base_url", BASE_URL, 
                   "--model", MODEL]
        },
        {
            "name": "Dataset lớn (1000 hội thoại, cân bằng)",
            "cmd": [sys.executable, str(generator_script), 
                   "--total", "1000", 
                   "--api_key", API_KEY, 
                   "--base_url", BASE_URL, 
                   "--model", MODEL]
        },
        {
            "name": "Chỉ hội thoại lừa đảo (200)",
            "cmd": [sys.executable, str(generator_script), 
                   "--fraud_only", "200", 
                   "--api_key", API_KEY, 
                   "--base_url", BASE_URL, 
                   "--model", MODEL]
        },
        {
            "name": "Chỉ hội thoại bình thường (300)",
            "cmd": [sys.executable, str(generator_script), 
                   "--normal_only", "300", 
                   "--api_key", API_KEY, 
                   "--base_url", BASE_URL, 
                   "--model", MODEL]
        }
    ]
    
    # Hiển thị menu
    for i, config in enumerate(configs, 1):
        print(f"{i}. {config['name']}")
    
    print("0. Thoát")
    print("=" * 50)
    
    try:
        choice = int(input("Chọn cấu hình (0-5): "))
        
        if choice == 0:
            print("👋 Thoát!")
            return
        
        if 1 <= choice <= len(configs):
            config = configs[choice - 1]
            success = run_command(config["cmd"], config["name"])
            
            if success:
                print(f"\n🎉 Hoàn thành sinh dataset: {config['name']}")
                print(f"📁 Kiểm tra thư mục: D:\\Du-an\\TeleAntiFraud\\multi-agents-tools\\dataset")
            else:
                print(f"\n❌ Sinh dataset thất bại")
        else:
            print("❌ Lựa chọn không hợp lệ!")
            
    except ValueError:
        print("❌ Vui lòng nhập số!")
    except KeyboardInterrupt:
        print("\n❌ Bị hủy bởi người dùng!")

if __name__ == "__main__":
    main()
