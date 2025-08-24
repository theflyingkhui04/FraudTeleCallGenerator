#!/usr/bin/env python3
"""
🎵 Voice Dataset Generator
Chuyển đổi text conversations thành MP3 audio files bằng gTTS

Author: FraudTeleCallGenerator Team
Usage: python wav_audio_generator.py --dataset input.jsonl --output voice_dataset
"""

import json
import os
import sys
from pathlib import Path
import argparse
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm
import wave
import struct

# Use gTTS as fallback TTS solution
try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WavAudioGenerator:
    """Simple audio generator that saves directly to WAV format"""
    
    def __init__(self, output_dir: str = "audio_dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not TTS_AVAILABLE:
            logger.error("gTTS not installed. Run: pip install gtts")
            sys.exit(1)
    
    def synthesize_with_gtts(self, text: str, role: str) -> Optional[str]:
        """Generate audio using Google TTS and save directly as WAV"""
        # Clean text for TTS
        text = text.strip()
        if not text:
            return None
        
        # Create temporary MP3 file
        temp_mp3 = self.output_dir / f"temp_{role}_{int(time.time() * 1000)}.mp3"
        
        try:
            # Generate TTS
            tts = gTTS(text=text, lang='vi', slow=False)
            tts.save(str(temp_mp3))
            
            # Add delay to ensure file is written
            time.sleep(0.2)
            
            # Check if file exists
            if not temp_mp3.exists():
                logger.error(f"TTS file not created: {temp_mp3}")
                return None
            
            # For now, just return the MP3 path
            # We'll convert to WAV later when we have proper audio tools
            return str(temp_mp3)
            
        except Exception as e:
            logger.error(f"TTS failed for role {role}: {e}")
            if temp_mp3.exists():
                try:
                    temp_mp3.unlink()
                except:
                    pass
            return None
    
    def process_conversation(self, conversation: Dict, conv_id: str) -> Dict:
        """Process a single conversation"""
        results = {
            "conversation_id": conv_id,
            "audio_files": [],
            "metadata": conversation.get("metadata", {}),
            "processing_time": 0,
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            # Create conversation directory
            conv_dir = self.output_dir / conv_id
            conv_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each message
            dialogue_history = conversation.get("dialogue_history", [])
            
            for i, message in enumerate(dialogue_history):
                try:
                    role = message["role"]
                    content = message["content"]
                    
                    # Generate audio
                    audio_file = self.synthesize_with_gtts(content, role)
                    
                    if audio_file:
                        # Move to final location
                        final_filename = f"msg_{i:03d}_{role}.mp3"
                        final_filepath = conv_dir / final_filename
                        
                        # Move temp file to final location
                        temp_path = Path(audio_file)
                        if temp_path.exists():
                            temp_path.rename(final_filepath)
                            
                            # Record metadata
                            results["audio_files"].append({
                                "message_index": i,
                                "role": role,
                                "audio_file": str(final_filepath),
                                "text": content[:100] + "..." if len(content) > 100 else content,
                                "timestamp": message.get("timestamp"),
                                "format": "mp3"
                            })
                        else:
                            logger.error(f"Temp audio file not found: {audio_file}")
                    
                except Exception as e:
                    error_msg = f"Failed to process message {i}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Save conversation metadata
            metadata_file = conv_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            results["processing_time"] = time.time() - start_time
            logger.info(f"✅ Processed conversation {conv_id} with {len(results['audio_files'])} audio files in {results['processing_time']:.2f}s")
            
        except Exception as e:
            error_msg = f"Failed to process conversation {conv_id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def generate_audio_dataset(self, dataset_path: str, max_workers: int = 1, 
                             limit: Optional[int] = None) -> Dict:
        """Generate audio dataset from converted text conversations"""
        logger.info(f"🎵 Starting audio generation from {dataset_path}")
        
        # Load dataset
        conversations = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    conv = json.loads(line.strip())
                    conversations.append(conv)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON at line {line_num}: {e}")
                    continue
        
        if limit:
            conversations = conversations[:limit]
            logger.info(f"Limited to {limit} conversations")
        
        # Process conversations
        results = []
        errors = []
        
        # Use single worker to avoid file conflicts
        for i, conv in enumerate(tqdm(conversations, desc="Generating audio")):
            try:
                result = self.process_conversation(
                    conv, 
                    conv.get("tts_id", f"conv_{i:05d}")
                )
                results.append(result)
                
                if result["errors"]:
                    errors.extend(result["errors"])
                
            except Exception as e:
                error_msg = f"Worker failed for conversation {i}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Generate summary
        summary = {
            "total_conversations": len(conversations),
            "successful": len([r for r in results if not r["errors"]]),
            "failed": len([r for r in results if r["errors"]]),
            "total_errors": len(errors),
            "output_directory": str(self.output_dir),
            "processing_time": sum(r["processing_time"] for r in results),
            "total_audio_files": sum(len(r["audio_files"]) for r in results),
            "errors": errors[:10]  # First 10 errors
        }
        
        # Save summary
        summary_file = self.output_dir / "generation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🎉 Audio generation completed!")
        logger.info(f"✅ Successful: {summary['successful']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"🎵 Total audio files: {summary['total_audio_files']}")
        logger.info(f"📁 Output: {summary['output_directory']}")
        
        return summary

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate audio from converted dataset")
    parser.add_argument("--dataset", required=True, help="Path to converted JSONL dataset file")
    parser.add_argument("--output", default="audio_dataset", help="Output directory")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers")
    parser.add_argument("--limit", type=int, help="Limit number of conversations")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = WavAudioGenerator(output_dir=args.output)
        
        # Generate audio dataset
        summary = generator.generate_audio_dataset(
            dataset_path=args.dataset,
            max_workers=args.workers,
            limit=args.limit
        )
        
        print(f"\n🎉 Audio generation completed!")
        print(f"✅ Successful: {summary['successful']}/{summary['total_conversations']}")
        print(f"🎵 Total audio files: {summary['total_audio_files']}")
        print(f"📁 Output: {summary['output_directory']}")
        
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
