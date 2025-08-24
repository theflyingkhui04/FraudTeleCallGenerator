#!/usr/bin/env python3
"""
Convert existing dataset format to audio-generation compatible format
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetFormatConverter:
    """Convert dataset from current format to audio-generation format"""
    
    def __init__(self):
        self.converted_count = 0
        self.error_count = 0
    
    def convert_conversation(self, conversation: Dict) -> Dict:
        """Convert single conversation to audio format"""
        try:
            # Extract dialogue history from left/right format
            left_messages = conversation.get("left", [])
            right_messages = conversation.get("right", [])
            
            # Create interleaved dialogue history
            dialogue_history = []
            max_length = max(len(left_messages), len(right_messages))
            
            for i in range(max_length):
                # Add left message (scammer/service)
                if i < len(left_messages):
                    dialogue_history.append({
                        "role": "left",
                        "content": left_messages[i],
                        "timestamp": f"msg_{len(dialogue_history):03d}"
                    })
                
                # Add right message (victim/customer)  
                if i < len(right_messages):
                    dialogue_history.append({
                        "role": "right", 
                        "content": right_messages[i],
                        "timestamp": f"msg_{len(dialogue_history):03d}"
                    })
            
            # Create converted conversation
            converted = {
                "tts_id": conversation.get("tts_id", f"conv_{self.converted_count:05d}"),
                "dialogue_history": dialogue_history,
                "metadata": {
                    "total_messages": len(dialogue_history),
                    "fraud_type": conversation.get("fraud_type"),
                    "conversation_type": conversation.get("conversation_type"),
                    "is_fraud": conversation.get("is_fraud", conversation.get("label") == "fraud"),
                    "user_age": conversation.get("user_age"),
                    "user_awareness": conversation.get("user_awareness"),
                    "occupation": conversation.get("occupation"),
                    "termination_reason": conversation.get("termination_reason"),
                    "terminator": conversation.get("terminator")
                },
                "original_format": {
                    "left_count": len(left_messages),
                    "right_count": len(right_messages)
                }
            }
            
            self.converted_count += 1
            return converted
            
        except Exception as e:
            logger.error(f"Error converting conversation: {e}")
            self.error_count += 1
            return None
    
    def convert_dataset(self, input_path: str, output_path: str) -> Dict:
        """Convert entire dataset file"""
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Create output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting dataset: {input_path} -> {output_path}")
        
        converted_conversations = []
        
        # Read and convert each conversation
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    conversation = json.loads(line.strip())
                    converted = self.convert_conversation(conversation)
                    
                    if converted:
                        converted_conversations.append(converted)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error at line {line_num}: {e}")
                    self.error_count += 1
                except Exception as e:
                    logger.error(f"Conversion error at line {line_num}: {e}")
                    self.error_count += 1
        
        # Write converted dataset
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in converted_conversations:
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        # Generate summary
        summary = {
            "input_file": str(input_file),
            "output_file": str(output_file),
            "total_conversations": len(converted_conversations),
            "successful_conversions": self.converted_count,
            "failed_conversions": self.error_count,
            "conversion_rate": f"{(self.converted_count / (self.converted_count + self.error_count) * 100):.2f}%" if (self.converted_count + self.error_count) > 0 else "0%"
        }
        
        # Save summary
        summary_file = output_file.parent / f"{output_file.stem}_conversion_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Conversion completed: {self.converted_count} successful, {self.error_count} failed")
        logger.info(f"📊 Summary saved: {summary_file}")
        
        return summary

def main():
    parser = argparse.ArgumentParser(description="Convert dataset format for audio generation")
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    
    args = parser.parse_args()
    
    try:
        converter = DatasetFormatConverter()
        summary = converter.convert_dataset(args.input, args.output)
        
        print(f"\n🎉 Dataset conversion completed!")
        print(f"✅ Successful: {summary['successful_conversions']}")
        print(f"❌ Failed: {summary['failed_conversions']}")
        print(f"📁 Output: {summary['output_file']}")
        
    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
