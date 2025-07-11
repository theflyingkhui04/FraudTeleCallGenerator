"""
Text-to-Speech Generator for Fraud Detection Dataset
Converts conversation dialogues to voice files using Gemini API
"""

import json
import os
import sys
import subprocess
import base64
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
import time
import random

# import google.generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Alternative TTS imports
try:
    import pyttsx3  # Offline TTS
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS  # Google TTS (online)
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


@dataclass
class VoiceConfig:
    """Configuration for voice generation"""
    voice_type: str  # "male_professional", "female_young", etc.
    speed: float = 1.0  # Speech speed multiplier
    pitch: float = 1.0  # Pitch adjustment
    emotion: str = "neutral"  # "urgent", "confident", "confused", etc.


@dataclass
class AudioMetadata:
    """Metadata for generated audio"""
    conversation_id: str
    turn_number: int
    speaker: str
    text_content: str
    voice_config: VoiceConfig
    file_path: str
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    generation_timestamp: float = 0.0


class VoiceAssigner:
    """Handles voice assignment strategy for different speaker types"""
    
    def __init__(self):
        self.voice_mappings = {
            # Fraud conversation voices
            "left": {  # Usually scammer
                "voice_type": "male_professional",
                "emotion": "confident",
                "speed": 1.1  # Slightly faster for urgency
            },
            "right": {  # Usually victim
                "voice_type": "female_young", 
                "emotion": "confused",
                "speed": 0.95  # Slightly slower for uncertainty
            }
        }
        
        # Track voice consistency per conversation
        self.conversation_voices: Dict[str, Dict[str, VoiceConfig]] = {}
    
    def assign_voice(self, conversation_id: str, speaker: str, text: str, 
                    conversation_type: str = "fraud") -> VoiceConfig:
        """Assign consistent voice for speaker in conversation"""
        
        if conversation_id not in self.conversation_voices:
            self.conversation_voices[conversation_id] = {}
        
        if speaker in self.conversation_voices[conversation_id]:
            return self.conversation_voices[conversation_id][speaker]
        
        # Create new voice config
        base_config = self.voice_mappings.get(speaker, self.voice_mappings["right"])
        
        # Adjust for conversation type
        if conversation_type == "fraud":
            if speaker == "left":  # Scammer
                emotion = self._detect_scammer_emotion(text)
                speed = 1.1 if "urgent" in emotion else 1.0
            else:  # Victim
                emotion = self._detect_victim_emotion(text)
                speed = 0.95 if "confused" in emotion else 1.0
        else:  # Normal conversation
            emotion = "professional"
            speed = 1.0
        
        voice_config = VoiceConfig(
            voice_type=base_config["voice_type"],
            emotion=emotion,
            speed=speed,
            pitch=1.0
        )
        
        self.conversation_voices[conversation_id][speaker] = voice_config
        return voice_config
    
    def _detect_scammer_emotion(self, text: str) -> str:
        """Detect emotional context for scammer speech"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["khẩn cấp", "nhanh", "gấp", "ngay"]):
            return "urgent"
        elif any(word in text_lower for word in ["chắc chắn", "tin tưởng", "cam kết"]):
            return "confident"
        elif any(word in text_lower for word in ["ưu đãi", "cơ hội", "đặc biệt"]):
            return "persuasive"
        
        return "professional"
    
    def _detect_victim_emotion(self, text: str) -> str:
        """Detect emotional context for victim speech"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["sợ", "lo", "không chắc", "hoang mang"]):
            return "worried"
        elif any(word in text_lower for word in ["không hiểu", "thế nào", "là sao"]):
            return "confused"
        elif any(word in text_lower for word in ["được không", "có thể", "cho em hỏi"]):
            return "polite"
        
        return "neutral"


class RealTTSClient:
    """Client for Real Text-to-Speech using available TTS engines"""
    
    def __init__(self, api_key: str = None, engine: str = "auto"):
        self.api_key = api_key
        self.engine = self._detect_best_engine(engine)
        self.setup_client()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
    def _detect_best_engine(self, preference: str) -> str:
        """Detect best available TTS engine"""
        if preference == "gtts" and GTTS_AVAILABLE:
            return "gtts"
        elif preference == "pyttsx3" and PYTTSX3_AVAILABLE:
            return "pyttsx3"
        elif preference == "auto":
            if GTTS_AVAILABLE:
                return "gtts"  # Prefer online TTS for better quality
            elif PYTTSX3_AVAILABLE:
                return "pyttsx3"
            else:
                return "mock"  # Fallback to mock
        else:
            return "mock"
        
    def setup_client(self):
        """Initialize TTS client based on engine"""
        if self.engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            self.pyttsx3_engine = pyttsx3.init()
            
            # Configure Vietnamese voice if available
            voices = self.pyttsx3_engine.getProperty('voices')
            for voice in voices:
                if 'vi' in voice.id.lower() or 'vietnam' in voice.name.lower():
                    self.pyttsx3_engine.setProperty('voice', voice.id)
                    break
                    
        elif self.engine == "gtts":
            # gTTS doesn't need initialization
            pass
        else:
            # Mock engine
            logging.warning("No TTS engine available, using mock audio")
    
    def text_to_speech(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Convert text to speech using selected engine"""
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        try:
            if self.engine == "gtts":
                return self._gtts_generate(text, voice_config)
            elif self.engine == "pyttsx3":
                return self._pyttsx3_generate(text, voice_config)
            else:
                return self._mock_generate(text, voice_config)
                
        except Exception as e:
            logging.error(f"TTS generation failed: {e}")
            # Fallback to mock
            return self._mock_generate(text, voice_config)
        finally:
            self.last_request_time = time.time()
    
    def _gtts_generate(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Generate speech using Google TTS"""
        # Configure gTTS
        slow = voice_config.speed < 1.0
        
        # Create TTS object
        tts = gTTS(text=text, lang='vi', slow=slow)
        
        # Save to memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return audio_buffer.read()
    
    def _pyttsx3_generate(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Generate speech using pyttsx3"""
        # Configure voice properties
        self.pyttsx3_engine.setProperty('rate', int(200 * voice_config.speed))
        
        # Generate to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        # Save speech to file
        self.pyttsx3_engine.save_to_file(text, temp_path)
        self.pyttsx3_engine.runAndWait()
        
        # Read file content
        with open(temp_path, 'rb') as f:
            audio_data = f.read()
        
        # Clean up
        os.unlink(temp_path)
        
        return audio_data
    
    def _mock_generate(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Generate mock audio data (fallback)"""
        logging.warning(f"Using mock audio for: {text[:50]}...")
        
        duration = len(text) * 0.1  # Rough estimate: 100ms per character
        duration *= (1.0 / voice_config.speed)  # Adjust for speed
        
        # Simulate audio file header + data
        sample_rate = 22050
        samples = int(duration * sample_rate)
        
        # Create mock WAV header
        header = b'RIFF' + (36 + samples * 2).to_bytes(4, 'little') + b'WAVE'
        header += b'fmt ' + (16).to_bytes(4, 'little')
        header += (1).to_bytes(2, 'little')  # PCM format
        header += (1).to_bytes(2, 'little')  # Mono
        header += sample_rate.to_bytes(4, 'little')
        header += (sample_rate * 2).to_bytes(4, 'little')  # Byte rate
        header += (2).to_bytes(2, 'little')  # Block align
        header += (16).to_bytes(2, 'little')  # Bits per sample
        header += b'data' + (samples * 2).to_bytes(4, 'little')
        
        # Generate sine wave instead of random noise for better audio
        import math
        frequency = 440  # A4 note
        audio_data = []
        for i in range(samples):
            # Generate sine wave
            sample = int(32767 * 0.1 * math.sin(2 * math.pi * frequency * i / sample_rate))
            # Convert to 16-bit little-endian
            audio_data.extend(sample.to_bytes(2, 'little', signed=True))
        
        return header + bytes(audio_data)


class TTSDatasetGenerator:
    """Main class for generating TTS dataset from text conversations"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.model = model
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup paths
        self.current_dir = Path(__file__).parent
        self.project_root = self.current_dir.parent
        self.dataset_dir = self.project_root / "dataset"
        self.output_dir = self.current_dir / f"voice_dataset_{self.timestamp}"
        
        # Initialize components
        self.tts_client = RealTTSClient(api_key)
        self.voice_assigner = VoiceAssigner()
        
        # Setup logging
        self.setup_logging()
        
        # Create output directories
        self.setup_output_directories()
        
        # Metadata tracking
        self.generated_audio: List[AudioMetadata] = []
        self.statistics = {
            "total_conversations": 0,
            "total_turns": 0,
            "total_audio_files": 0,
            "total_duration_seconds": 0.0,
            "total_size_bytes": 0,
            "processing_errors": 0
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.current_dir / f"tts_generation_{self.timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def setup_output_directories(self):
        """Create output directory structure"""
        directories = [
            self.output_dir,
            self.output_dir / "fraud_audio",
            self.output_dir / "normal_audio", 
            self.output_dir / "metadata",
            self.output_dir / "fraud_audio" / "conversations",
            self.output_dir / "normal_audio" / "conversations"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.logger.info(f"Created output directories at: {self.output_dir}")
    
    def process_conversation_file(self, file_path: Path, conversation_type: str) -> List[AudioMetadata]:
        """Process a single conversation file to generate audio"""
        
        self.logger.info(f"Processing conversation file: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
            
            dialogue_history = conversation_data.get("dialogue_history", [])
            conversation_id = file_path.stem  # Use filename as conversation ID
            
            audio_metadata_list = []
            
            # Create conversation subdirectory
            conv_dir = self.output_dir / f"{conversation_type}_audio" / "conversations" / conversation_id
            conv_dir.mkdir(parents=True, exist_ok=True)
            
            for turn_idx, turn in enumerate(dialogue_history):
                try:
                    speaker = turn["role"]
                    text = turn["content"]
                    
                    if not text.strip():
                        continue
                    
                    # Assign voice configuration
                    voice_config = self.voice_assigner.assign_voice(
                        conversation_id, speaker, text, conversation_type
                    )
                    
                    # Generate audio
                    audio_data = self.tts_client.text_to_speech(text, voice_config)
                    
                    # Save audio file
                    audio_filename = f"turn_{turn_idx:03d}_{speaker}.wav"
                    audio_path = conv_dir / audio_filename
                    
                    with open(audio_path, 'wb') as af:
                        af.write(audio_data)
                    
                    # Calculate file statistics
                    file_size = len(audio_data)
                    duration = self._estimate_duration(text, voice_config.speed)
                    
                    # Create metadata
                    metadata = AudioMetadata(
                        conversation_id=conversation_id,
                        turn_number=turn_idx,
                        speaker=speaker,
                        text_content=text,
                        voice_config=voice_config,
                        file_path=str(audio_path.relative_to(self.output_dir)),
                        duration_seconds=duration,
                        file_size_bytes=file_size,
                        generation_timestamp=time.time()
                    )
                    
                    audio_metadata_list.append(metadata)
                    self.generated_audio.append(metadata)
                    
                    # Update statistics
                    self.statistics["total_turns"] += 1
                    self.statistics["total_audio_files"] += 1
                    self.statistics["total_duration_seconds"] += duration
                    self.statistics["total_size_bytes"] += file_size
                    
                    self.logger.info(f"Generated audio for turn {turn_idx}: {audio_filename}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing turn {turn_idx}: {e}")
                    self.statistics["processing_errors"] += 1
                    continue
            
            self.statistics["total_conversations"] += 1
            return audio_metadata_list
            
        except Exception as e:
            self.logger.error(f"Error processing conversation file {file_path}: {e}")
            self.statistics["processing_errors"] += 1
            return []
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length and speed"""
        # Rough estimate: average Vietnamese speaking rate is ~150 words per minute
        # Adjust for character count and speed
        char_count = len(text)
        base_duration = char_count * 0.08  # ~80ms per character
        return base_duration / speed
    
    def process_dataset_batch(self, conversation_type: str, max_files: int = 5) -> Dict[str, Any]:
        """Process a batch of conversation files"""
        
        # Find conversation files
        if conversation_type == "fraud":
            source_dir = self.dataset_dir / "fraud_20250705_061032" / "full_dialogues"
        else:
            source_dir = self.dataset_dir / "normal_20250705_061032" / "full_dialogues"
        
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        # Get list of conversation files
        conversation_files = list(source_dir.glob("*.json"))[:max_files]
        
        self.logger.info(f"Processing {len(conversation_files)} {conversation_type} conversations")
        
        all_metadata = []
        for file_path in conversation_files:
            metadata_list = self.process_conversation_file(file_path, conversation_type)
            all_metadata.extend(metadata_list)
        
        # Generate combined audio files per conversation
        self._generate_combined_conversations(conversation_type, all_metadata)
        
        return {
            "conversation_type": conversation_type,
            "processed_files": len(conversation_files),
            "generated_audio_files": len(all_metadata),
            "output_directory": str(self.output_dir / f"{conversation_type}_audio")
        }
    
    def _generate_combined_conversations(self, conversation_type: str, metadata_list: List[AudioMetadata]):
        """Generate combined audio files for each conversation"""
        
        # Group metadata by conversation
        conversations = {}
        for metadata in metadata_list:
            conv_id = metadata.conversation_id
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append(metadata)
        
        # For each conversation, we would combine individual turn audio files
        # This is a placeholder - actual implementation would use audio processing library
        for conv_id, conv_metadata in conversations.items():
            self.logger.info(f"Would combine {len(conv_metadata)} audio files for conversation {conv_id}")
    
    def generate_metadata_report(self) -> Dict[str, Any]:
        """Generate comprehensive metadata report"""
        
        report = {
            "generation_info": {
                "timestamp": self.timestamp,
                "model": self.model,
                "total_conversations": self.statistics["total_conversations"],
                "total_audio_files": self.statistics["total_audio_files"],
                "total_duration_minutes": round(self.statistics["total_duration_seconds"] / 60, 2),
                "total_size_mb": round(self.statistics["total_size_bytes"] / (1024 * 1024), 2),
                "processing_errors": self.statistics["processing_errors"]
            },
            "voice_assignments": {},
            "audio_files": []
        }
        
        # Add voice assignment summary
        for conv_id, speakers in self.voice_assigner.conversation_voices.items():
            report["voice_assignments"][conv_id] = {
                speaker: {
                    "voice_type": config.voice_type,
                    "emotion": config.emotion,
                    "speed": config.speed
                }
                for speaker, config in speakers.items()
            }
        
        # Add audio file details
        for metadata in self.generated_audio:
            report["audio_files"].append({
                "conversation_id": metadata.conversation_id,
                "turn_number": metadata.turn_number,
                "speaker": metadata.speaker,
                "file_path": metadata.file_path,
                "duration_seconds": metadata.duration_seconds,
                "file_size_bytes": metadata.file_size_bytes,
                "voice_type": metadata.voice_config.voice_type,
                "emotion": metadata.voice_config.emotion
            })
        
        # Save report
        report_path = self.output_dir / "metadata" / "generation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Generated metadata report: {report_path}")
        return report
    
    def run_test_generation(self, fraud_files: int = 2, normal_files: int = 2) -> Dict[str, Any]:
        """Run a test generation with limited files"""
        
        self.logger.info(f"Starting test TTS generation (fraud: {fraud_files}, normal: {normal_files})")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "fraud_results": None,
            "normal_results": None,
            "metadata_report": None,
            "status": "started"
        }
        
        try:
            # Process fraud conversations
            if fraud_files > 0:
                results["fraud_results"] = self.process_dataset_batch("fraud", fraud_files)
            
            # Process normal conversations  
            if normal_files > 0:
                results["normal_results"] = self.process_dataset_batch("normal", normal_files)
            
            # Generate final report
            results["metadata_report"] = self.generate_metadata_report()
            
            results["status"] = "completed"
            results["end_time"] = datetime.now().isoformat()
            
            self.logger.info("Test TTS generation completed successfully")
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["end_time"] = datetime.now().isoformat()
            
            self.logger.error(f"Test TTS generation failed: {e}")
        
        return results


def main():
    """Main function for testing TTS generation"""
    
    # Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return
    
    # Initialize generator
    generator = TTSDatasetGenerator(api_key)
    
    # Run test with small batch
    results = generator.run_test_generation(fraud_files=1, normal_files=1)
    
    print("\n" + "="*50)
    print("TTS GENERATION TEST RESULTS")
    print("="*50)
    print(f"Status: {results['status']}")
    print(f"Start time: {results['start_time']}")
    print(f"End time: {results.get('end_time', 'N/A')}")
    
    if results["fraud_results"]:
        print(f"\nFraud conversations: {results['fraud_results']['processed_files']} files")
        print(f"Fraud audio files: {results['fraud_results']['generated_audio_files']} files")
    
    if results["normal_results"]:
        print(f"\nNormal conversations: {results['normal_results']['processed_files']} files")
        print(f"Normal audio files: {results['normal_results']['generated_audio_files']} files")
    
    if results["metadata_report"]:
        report = results["metadata_report"]["generation_info"]
        print(f"\nTotal audio files: {report['total_audio_files']}")
        print(f"Total duration: {report['total_duration_minutes']} minutes")
        print(f"Total size: {report['total_size_mb']} MB")
        print(f"Processing errors: {report['processing_errors']}")
    
    if results["status"] == "failed":
        print(f"\nError: {results.get('error', 'Unknown error')}")
    
    print(f"\nOutput directory: {generator.output_dir}")


if __name__ == "__main__":
    main()
