#!/usr/bin/env python3
"""
Chuyển dataset dạng chữ thành audio sử dụng mô hình VITS
"""

import json
import os
import sys
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tqdm import tqdm

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from vits_client import VITSVietnameseTTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatasetAudioGenerator:
    """Generate audio from TeleAntiFraud dataset"""
    
    def __init__(self, model_path: str = "models", output_dir: str = "audio_dataset"):
        """
        Initialize audio generator
        
        Args:
            model_path: Path to VITS models
            output_dir: Output directory for audio files
        """
        self.tts = VITSVietnameseTTS(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Role mapping for voice selection
        self.role_mapping = {
            "left": "scammer",    # Left agent = scammer
            "right": "victim"     # Right agent = victim
        }
        
        # Emotion mapping based on content
        self.emotion_patterns = {
            "scammer": {
                "confident": ["tôi gọi từ", "chúng tôi", "cơ quan", "công an", "ngân hàng"],
                "authoritative": ["bạn phải", "cần phải", "yêu cầu", "bắt buộc"],
                "persuasive": ["tin tôi", "yên tâm", "đảm bảo", "cam kết"]
            },
            "victim": {
                "worried": ["lo lắng", "sợ", "hoang mang", "không hiểu"],
                "confused": ["sao", "tại sao", "làm sao", "như thế nào"],
                "scared": ["trời ơi", "không thể", "chết rồi", "mất tiền"]
            }
        }
    
    def detect_emotion(self, text: str, role: str) -> str:
        """Detect emotion from text content"""
        text_lower = text.lower()
        
        if role in self.emotion_patterns:
            for emotion, patterns in self.emotion_patterns[role].items():
                if any(pattern in text_lower for pattern in patterns):
                    return emotion
        
        # Default emotions
        return "confident" if role == "scammer" else "worried"
    
    def determine_voice_params(self, message: Dict, conversation_context: Dict) -> Dict:
        """Determine voice parameters based on message and context"""
        role = self.role_mapping.get(message["role"], "scammer")
        emotion = self.detect_emotion(message["content"], role)
        
        # Adjust speed based on emotion
        speed_mapping = {
            "confident": 1.0,
            "authoritative": 0.95,
            "persuasive": 0.9,
            "worried": 0.85,
            "confused": 0.8,
            "scared": 0.75
        }
        
        return {
            "role": role,
            "emotion": emotion,
            "speed": speed_mapping.get(emotion, 1.0)
        }
    
    def process_conversation(self, conversation: Dict, conv_id: str) -> Dict:
        """Process a single conversation"""
        results = {
            "conversation_id": conv_id,
            "audio_files": [],
            "metadata": {
                "total_messages": len(conversation["dialogue_history"]),
                "fraud_type": conversation.get("fraud_type", "unknown"),
                "is_fraud": conversation.get("is_fraud", True)
            },
            "processing_time": 0,
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            # Create conversation directory
            conv_dir = self.output_dir / conv_id
            conv_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each message
            for i, message in enumerate(conversation["dialogue_history"]):
                try:
                    # Determine voice parameters
                    voice_params = self.determine_voice_params(message, conversation)
                    
                    # Generate audio
                    audio = self.tts.synthesize(
                        text=message["content"],
                        role=voice_params["role"],
                        emotion=voice_params["emotion"],
                        speed=voice_params["speed"]
                    )
                    
                    # Save audio file
                    audio_filename = f"msg_{i:03d}_{voice_params['role']}.wav"
                    audio_filepath = conv_dir / audio_filename
                    
                    self.tts.save_audio(audio, str(audio_filepath))
                    
                    # Record metadata
                    results["audio_files"].append({
                        "message_index": i,
                        "role": message["role"],
                        "voice_role": voice_params["role"],
                        "emotion": voice_params["emotion"],
                        "speed": voice_params["speed"],
                        "audio_file": str(audio_filepath),
                        "text": message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"],
                        "timestamp": message.get("timestamp")
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to process message {i}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Save conversation metadata
            metadata_file = conv_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            results["processing_time"] = time.time() - start_time
            logger.info(f"✅ Processed conversation {conv_id} in {results['processing_time']:.2f}s")
            
        except Exception as e:
            error_msg = f"Failed to process conversation {conv_id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def load_dataset(self, dataset_path: str) -> List[Dict]:
        """Load dataset from JSONL file"""
        conversations = []
        
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        conv = json.loads(line.strip())
                        conversations.append(conv)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON at line {line_num}: {e}")
                        continue
            
            logger.info(f"✅ Loaded {len(conversations)} conversations from {dataset_path}")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    def generate_audio_dataset(self, dataset_path: str, max_workers: int = 2, 
                             limit: Optional[int] = None) -> Dict:
        """
        Generate audio dataset from text conversations
        
        Args:
            dataset_path: Path to JSONL dataset file
            max_workers: Number of parallel workers
            limit: Maximum number of conversations to process
            
        Returns:
            Processing summary
        """
        logger.info(f"🎵 Starting audio generation from {dataset_path}")
        
        # Load dataset
        conversations = self.load_dataset(dataset_path)
        
        if limit:
            conversations = conversations[:limit]
            logger.info(f"Limited to {limit} conversations")
        
        # Process conversations
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_conv = {
                executor.submit(
                    self.process_conversation, 
                    conv, 
                    f"conv_{i:05d}"
                ): i for i, conv in enumerate(conversations)
            }
            
            # Process results with progress bar
            with tqdm(total=len(conversations), desc="Generating audio") as pbar:
                for future in as_completed(future_to_conv):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result["errors"]:
                            errors.extend(result["errors"])
                        
                    except Exception as e:
                        conv_idx = future_to_conv[future]
                        error_msg = f"Worker failed for conversation {conv_idx}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                    
                    pbar.update(1)
        
        # Generate summary
        summary = {
            "total_conversations": len(conversations),
            "successful": len([r for r in results if not r["errors"]]),
            "failed": len([r for r in results if r["errors"]]),
            "total_errors": len(errors),
            "output_directory": str(self.output_dir),
            "processing_time": sum(r["processing_time"] for r in results),
            "errors": errors[:10]  # First 10 errors
        }
        
        # Save summary
        summary_file = self.output_dir / "generation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🎉 Audio generation completed!")
        logger.info(f"✅ Successful: {summary['successful']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"📁 Output: {summary['output_directory']}")
        
        return summary

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate audio from TeleAntiFraud dataset")
    parser.add_argument("--dataset", required=True, help="Path to JSONL dataset file")
    parser.add_argument("--output", default="audio_dataset", help="Output directory")
    parser.add_argument("--models", default="models", help="Path to VITS models")
    parser.add_argument("--workers", type=int, default=2, help="Number of parallel workers")
    parser.add_argument("--limit", type=int, help="Limit number of conversations")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = DatasetAudioGenerator(
            model_path=args.models,
            output_dir=args.output
        )
        
        # Generate audio dataset
        summary = generator.generate_audio_dataset(
            dataset_path=args.dataset,
            max_workers=args.workers,
            limit=args.limit
        )
        
        print(f"\n🎉 Audio generation completed!")
        print(f"✅ Successful: {summary['successful']}/{summary['total_conversations']}")
        print(f"📁 Output: {summary['output_directory']}")
        
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
