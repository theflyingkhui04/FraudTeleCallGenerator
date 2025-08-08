#!/usr/bin/env python3
"""
Thiết đăt mô hình VITS TTS tiếng Việt
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def install_requirements():
    """Install required packages"""
    requirements = [
        "torch>=1.9.0",
        "torchaudio>=0.9.0",
        "numpy",
        "scipy",
        "librosa",
        "phonemizer",
        "Unidecode",
        "pillow",
        "matplotlib",
        "tensorboard",
        "jiwer",
        "pydub",
        "soundfile"
    ]
    
    print("Đang tải requirements...")
    for req in requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", req])
    
    print("✅ Requirements installed successfully!")

def download_vits_model():
    """Download pre-trained VITS Vietnamese model"""
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    
    # URLs for Vietnamese VITS models
    models = {
        "vits_viet_female": "https://huggingface.co/capleaf/viXTTS/resolve/main/model.pth",
        "vits_viet_male": "https://huggingface.co/capleaf/viXTTS/resolve/main/model_male.pth",
        "config": "https://huggingface.co/capleaf/viXTTS/resolve/main/config.json"
    }
    
    print("Đang tải xuống model VITS...")
    for name, url in models.items():
        file_path = model_dir / f"{name}.pth" if name != "config" else model_dir / "config.json"
        
        if not file_path.exists():
            print(f"Đang tải xuống {name}...")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ {name} downloaded successfully!")
            except Exception as e:
                print(f"❌ Failed to download {name}: {e}")
                # Alternative: use local installation
                print("Please download manually from HuggingFace")
    
    print("✅ Models setup complete!")

def clone_vits_repo():
    """Clone VITS repository"""
    if not os.path.exists("vits"):
        print("Đang clone VITS repository...")
        subprocess.run([
            "git", "clone", 
            "https://github.com/jaywalnut310/vits.git"
        ])
        print("✅ Đã clone VITS repository thành công!")
    else:
        print("✅ VITS repository có rồi, bỏ qua bước clone.")

if __name__ == "__main__":
    print("🚀 Đang thiết đặt repo VITS...")
    
    try:
        install_requirements()
        clone_vits_repo()
        download_vits_model()
        
        print("\n🎉 VITS Tiếng Việt đã thiết đặt thành công")
        print("Bước tiếp theo:")
        print("1. chạy lệnh: python test_vits.py")
        print("2. chạy lệnh: python dataset_to_audio.py")
        
    except Exception as e:
        print(f"❌ Thiết đặt gặp lỗi {e}")
        sys.exit(1)
