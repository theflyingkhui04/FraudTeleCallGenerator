#!/usr/bin/env python3
"""
VITS Vietnamese TTS Client for Dataset
"""

import os
import sys
import json
import torch
import numpy as np
import scipy.io.wavfile as wav
from pathlib import Path
import logging
import re
from typing import Dict, List, Optional, Tuple

# Add VITS to path
sys.path.append(str(Path(__file__).parent / "vits"))

# Import VITS modules
try:
    import commons
    import utils
    from models import SynthesizerTrn
    from text.symbols import symbols
    from text import text_to_sequence
except ImportError as e:
    print(f"❌ VITS import error: {e}")
    print("Please run: python setup_vits.py")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VITSVietnameseTTS:
    """Client Text-to-Speech sử dụng mô hình VITS cho tiếng Việt"""
    
    def __init__(self, model_path: str = "models", device: str = "auto"):
        """
        Thiết lập mô hình VITS TTS
        
        Args:
            model_path: đường dẫn đến thư mục chứa mô hình VITS
            device: thiết bị chạy model ('cpu', 'cuda', or 'auto')
        """
        self.model_path = Path(model_path)
        self.device = self._get_device(device)
          # Voice configurations
        self.voice_configs = {
            "scammer": {
                "model": "vits_viet_female.pth",  # Use same model, different speaker_id
                "speaker_id": 0,
                "emotion": "confident",
                "speed": 1.0,
                "pitch": 1.0
            },
            "victim": {
                "model": "vits_viet_female.pth", 
                "speaker_id": 0,
                "emotion": "worried",
                "speed": 0.9,
                "pitch": 1.1
            }
        }
        
        self.models = {}
        self.configs = {}
        self._load_models()
    
    def _get_device(self, device: str) -> torch.device:
        """Get torch device"""
        if device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)
    
    def _load_models(self):
        """Tải model VITS"""
        try:
            # Tải model configuration
            config_path = self.model_path / "config.json"
            if not config_path.exists():
                raise FileNotFoundError(f"Không tìm thấy file thiết lập model: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.hps = utils.get_hparams_from_file(config_path)
            
            # Tải model cho từng vai trò
            for role, config in self.voice_configs.items():
                model_file = self.model_path / config["model"]
                
                if not model_file.exists():
                    logger.warning(f"Không tìm thấy model: {model_file}")
                    continue
                
                # Initialize model
                net_g = SynthesizerTrn(
                    len(symbols),
                    self.hps.data.filter_length // 2 + 1,
                    self.hps.train.segment_size // self.hps.data.hop_length,
                    **self.hps.model
                ).to(self.device)
                
                # Load checkpoint
                checkpoint = torch.load(model_file, map_location=self.device)
                net_g.load_state_dict(checkpoint['model'])
                net_g.eval()
                
                self.models[role] = net_g
                logger.info(f"✅ Tải thành công model {role}: {model_file}")
        
        except Exception as e:
            logger.error(f"Lỗi khi tải model: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """Tiền xử lý văn bản tiếng Việt"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle Vietnamese-specific preprocessing
        text = text.replace('à', 'à').replace('á', 'á')  # Normalize accents
        text = text.replace('...', ', ')  # Replace ellipsis
        text = text.replace('ạ', 'ạ')  # Ensure proper tone marks
        
        # Add pauses for natural speech
        text = text.replace(',', ', ')
        text = text.replace('.', '. ')
        text = text.replace('?', '? ')
        text = text.replace('!', '! ')
        
        return text
    
    def text_to_sequence_viet(self, text: str) -> List[int]:
        """Chuyển đổi văn bản sau khi clean sang chuỗi """
        # Preprocess text
        text = self.preprocess_text(text)
        
        # Convert to sequence (this might need adjustment based on your phonemizer)
        sequence = text_to_sequence(text, ['vietnamese_cleaners'])
        
        return sequence
    
    def synthesize(self, text: str, role: str = "scammer", 
                   emotion: str = None, speed: float = None) -> np.ndarray:
        """
        Tổng hợp giọng nói từ văn bản

        Args:
            text: Văn bản đầu vào
            role: Vai trò người nói ('scammer' hoặc 'victim')
            emotion: Chọn cảm xúc
            speed: Chọn tốc độ
            
        Returns:
            Dạng sóng âm thanh dưới dạng mảng numpy
        """
        if role not in self.models:
            raise ValueError(f"Vai trò '{role}' không có sẵn. Hiện có các vai trò: {list(self.models.keys())}")
        
        # Get model and config
        model = self.models[role]
        config = self.voice_configs[role]
        
        # Override parameters if provided
        if emotion:
            config = config.copy()
            config["emotion"] = emotion
        if speed:
            config = config.copy()
            config["speed"] = speed
        
        try:
            # Convert text to sequence
            sequence = self.text_to_sequence_viet(text)
            sequence = torch.LongTensor(sequence).unsqueeze(0).to(self.device)
            
            # Generate audio
            with torch.no_grad():
                audio = model.infer(
                    sequence,
                    sequence_length=torch.LongTensor([len(sequence[0])]).to(self.device),
                    noise_scale=0.667,  # Emotion control
                    noise_scale_w=0.8,   # Speed control
                    length_scale=1.0 / config["speed"]  # Speed adjustment
                )[0][0, 0].cpu().float().numpy()
            
            return audio
            
        except Exception as e:
            logger.error(f"Synthesis failed for role '{role}': {e}")
            raise
    
    def save_audio(self, audio: np.ndarray, filepath: str, 
                   sample_rate: int = 22050) -> None:
        """Lưu âm thanh ra dạng file WAV
        Args:
            audio: Dạng sóng âm thanh dưới dạng mảng numpy
            filepath: Đường dẫn lưu file WAV
            sample_rate: Tần số mẫu (mặc định 22050Hz)
        """
        # Normalize audio
        audio = audio / np.max(np.abs(audio))
        
        # Convert to int16
        audio = (audio * 32767).astype(np.int16)
        
        # Save
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        wav.write(filepath, sample_rate, audio)
        logger.info(f"✅ Audio saved: {filepath}")

def test_vits():
    """Test VITS TTS"""
    try:
        tts = VITSVietnameseTTS()
        
        # Test texts
        test_cases = [
            {
                "text": "Tôi gọi từ phòng cảnh sát điều tra tội phạm công nghệ cao",
                "role": "scammer",
                "filename": "test_scammer.wav"
            },
            {
                "text": "Trời ơi, sao lại có chuyện này? Tôi không hiểu gì hết",
                "role": "victim", 
                "filename": "test_victim.wav"
            }
        ]
        
        print("🎤 Đang test model VITS TTS...")
        for i, test in enumerate(test_cases):
            print(f"Đang tạo {test['role']} audio...")
            
            audio = tts.synthesize(
                text=test["text"],
                role=test["role"]
            )
            
            tts.save_audio(audio, f"test_output/{test['filename']}")
            print(f"✅ Đã gen ra: {test['filename']}")
        
        print("🎉 Đã hoàn thành test mô hình VITS TTS!")
        
    except Exception as e:
        print(f"❌ Lỗi {e} khi kiểm tra VITS TTS")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vits()
