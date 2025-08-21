#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tối ưu hóa việc sinh dataset với parallel processing và retry logic
Enhanced with Stratified Sampling Algorithm for realistic user profiles
"""

import os
import json
import random
import argparse
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# Import từ dự án
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from agents.left_agent import LeftAgent
from agents.right_agent import RightAgent
from agents.manager_agent import ManagerAgent
from logic.dialogue_orchestrator import DialogueOrchestrator
from utils.stratified_sampling import StratifiedSampler

class OptimizedDialogueGenerator:
    """Generator tối ưu với retry logic và rate limiting"""
    
    def __init__(self, api_key: str, model: str, max_workers: int = 3, delay: float = 2.0):
        self.api_key = api_key
        self.model = model
        self.max_workers = max_workers
        self.delay = delay
        
        # Initialize Stratified Sampler
        self.stratified_sampler = StratifiedSampler()
        
        # Cập nhật config
        config.GEMINI_API_KEY = api_key
        config.DEFAULT_MODEL = model
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def generate_single_dialogue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sinh một hội thoại với retry logic"""
        dialogue_id = params['dialogue_id']
        dialogue_type = params['type']  # 'fraud' hoặc 'normal'
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if dialogue_type == 'fraud':
                    result = self._generate_fraud_dialogue(params)
                else:
                    result = self._generate_normal_dialogue(params)
                
                if result and result.get('dialogue_history'):
                    result['dialogue_id'] = dialogue_id
                    result['generation_params'] = params
                    return result
                    
            except requests.exceptions.HTTPError as e:
                if "429" in str(e):  # Rate limit
                    wait_time = (2 ** attempt) * self.delay  # Exponential backoff
                    self.logger.warning(f"Rate limit hit for {dialogue_id}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"HTTP error for {dialogue_id}: {e}")
                    break
            except Exception as e:
                self.logger.error(f"Error generating dialogue {dialogue_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.delay)
                    continue
                break
        
        return {"error": f"Failed to generate dialogue {dialogue_id} after {max_retries} attempts"}
    
    def _generate_fraud_dialogue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sinh hội thoại lừa đảo"""
        left_agent = LeftAgent(
            model=self.model,
            api_key=self.api_key,
            fraud_type=params['fraud_type']
        )
        
        right_agent = RightAgent(
            model=self.model,
            api_key=self.api_key,
            user_profile={
                "age": params['age'],
                "awareness": params['awareness'],
                "occupation": params['occupation']
            }
        )
        
        manager_agent = ManagerAgent(
            model=self.model,
            api_key=self.api_key,
            strictness=params.get('strictness', 'medium')
        )
        
        orchestrator = DialogueOrchestrator(
            left_agent=left_agent,
            right_agent=right_agent,
            manager_agent=manager_agent,
            max_turns=params.get('max_turns', 25)
        )
        
        result = orchestrator.run_dialogue()
        
        # Thêm delay để tránh rate limit
        time.sleep(self.delay)
        
        return result
    
    def _generate_normal_dialogue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sinh hội thoại bình thường (cần implement tương tự NormalTeleCallGenerator)"""
        # Tạm thời return empty result - cần implement based on normal dialogue logic
        self.logger.warning("Normal dialogue generation not implemented in this optimized version")
        return {"dialogue_history": [], "type": "normal"}
    
    def generate_fraud_batch(self, count: int, output_file: str, use_stratified: bool = True) -> Dict[str, Any]:
        """
        Sinh batch hội thoại lừa đảo với tùy chọn stratified sampling
        Args:
            count: Số lượng hội thoại cần sinh
            output_file: File đầu ra
            use_stratified: Sử dụng stratified sampling hay không
        """
        self.logger.info(f"🎯 Generating {count} fraud dialogues...")
        self.logger.info(f"📊 Sampling method: {'Stratified' if use_stratified else 'Random'}")
        
        if use_stratified:
            tasks = create_fraud_tasks_stratified(count, self.stratified_sampler)
        else:
            tasks = create_fraud_tasks(count)
        
        return self.generate_batch(tasks, output_file)
    
    def generate_batch(self, tasks: List[Dict[str, Any]], output_file: str) -> Dict[str, Any]:
        """Sinh batch hội thoại với parallel processing"""
        self.logger.info(f"Starting batch generation: {len(tasks)} tasks")
        
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.generate_single_dialogue, task): task 
                for task in tasks
            }
            
            # Process results with progress bar
            for future in tqdm(as_completed(future_to_task), total=len(tasks), desc="Generating dialogues"):
                task = future_to_task[future]
                try:
                    result = future.result()
                    if "error" not in result:
                        results.append(result)
                    else:
                        errors.append({"task": task, "error": result["error"]})
                except Exception as e:
                    errors.append({"task": task, "error": str(e)})
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                # Convert to simplified format for JSONL
                simplified = {
                    "dialogue_id": result.get('dialogue_id'),
                    "left": [msg['content'] for msg in result.get('dialogue_history', []) if msg['role'] == 'left'],
                    "right": [msg['content'] for msg in result.get('dialogue_history', []) if msg['role'] == 'right'],
                    "type": result.get('generation_params', {}).get('type', 'unknown'),
                    "fraud_type": result.get('generation_params', {}).get('fraud_type'),
                    "user_age": result.get('generation_params', {}).get('age'),
                    "user_awareness": result.get('generation_params', {}).get('awareness'),
                    "occupation": result.get('generation_params', {}).get('occupation'),
                    "termination_reason": result.get('termination_reason', ''),
                    "terminator": result.get('terminator', 'unknown')
                }
                f.write(json.dumps(simplified, ensure_ascii=False) + '\n')
        
        return {
            "success_count": len(results),
            "error_count": len(errors),
            "errors": errors,
            "output_file": output_file
        }

def create_fraud_tasks_stratified(count: int, sampler: Optional[StratifiedSampler] = None) -> List[Dict[str, Any]]:
    """
    Tạo tasks cho hội thoại lừa đảo với Stratified Sampling
    Enhanced với weighted occupation selection theo fraud type
    """
    if sampler is None:
        sampler = StratifiedSampler()
    
    tasks = []
    fraud_types = config.FRAUD_TYPES
    strictness_levels = ["low", "medium", "high"]
    
    # Tạo phân phối cân bằng cho các fraud types
    fraud_distribution = {}
    base_count = count // len(fraud_types)
    remainder = count % len(fraud_types)
    
    for i, fraud_type in enumerate(fraud_types):
        fraud_distribution[fraud_type] = base_count + (1 if i < remainder else 0)
    
    # Tạo user profiles với stratified sampling
    user_profiles = sampler.generate_batch_profiles(fraud_distribution)
    
    # Tạo tasks từ profiles
    for i, profile in enumerate(user_profiles):
        task = {
            "dialogue_id": f"fraud_{i+1:05d}",
            "type": "fraud",
            "fraud_type": profile["fraud_type"],
            "age": profile["age"],
            "awareness": profile["awareness"],
            "occupation": profile["occupation"],
            "strictness": random.choice(strictness_levels),
            "max_turns": random.randint(20, 30),
            # Thêm metadata cho phân tích
            "age_range": profile["age_range"],
            "sampling_method": "stratified_weighted"
        }
        tasks.append(task)
    
    # Log sampling statistics
    stats = sampler.analyze_profile_distribution(user_profiles)
    quality = sampler.validate_sampling_quality(user_profiles)
    
    print(f"📊 Stratified Sampling Statistics:")
    print(f"   Quality Score: {quality['quality_score']:.1f}%")
    print(f"   Realistic Combinations: {quality['realistic_combinations']}/{quality['total_profiles']}")
    
    return tasks

def create_fraud_tasks(count: int) -> List[Dict[str, Any]]:
    """Tạo tasks cho hội thoại lừa đảo (legacy method - random sampling)"""
    tasks = []
    fraud_types = config.FRAUD_TYPES
    occupations = config.OCCUPATIONS
    awareness_levels = config.AWARENESS_LEVELS
    
    age_ranges = [(18, 30), (31, 45), (46, 60), (61, 75)]
    strictness_levels = ["low", "medium", "high"]
    
    for i in range(count):
        age_range = random.choice(age_ranges)
        age = random.randint(age_range[0], age_range[1])
        
        task = {
            "dialogue_id": f"fraud_{i+1:05d}",
            "type": "fraud",
            "fraud_type": random.choice(fraud_types),
            "age": age,
            "awareness": random.choice(awareness_levels),
            "occupation": random.choice(occupations),
            "strictness": random.choice(strictness_levels),
            "max_turns": random.randint(20, 30),
            "sampling_method": "random"
        }
        tasks.append(task)
    
    return tasks

def create_normal_tasks(count: int) -> List[Dict[str, Any]]:
    """Tạo tasks cho hội thoại bình thường"""
    tasks = []
    conversation_types = config.CONVERSATION_TYPES
    occupations = config.OCCUPATIONS
    awareness_levels = config.AWARENESS_LEVELS
    
    age_ranges = [(18, 30), (31, 45), (46, 60), (61, 75)]
    
    for i in range(count):
        age_range = random.choice(age_ranges)
        age = random.randint(age_range[0], age_range[1])
        
        task = {
            "dialogue_id": f"normal_{i+1:05d}",
            "type": "normal",
            "conversation_type": random.choice(conversation_types),
            "age": age,
            "awareness": random.choice(awareness_levels),
            "occupation": random.choice(occupations),
            "max_turns": random.randint(15, 25)
        }
        tasks.append(task)
    
    return tasks

def main():
    parser = argparse.ArgumentParser(description="Enhanced dialogue generation with Stratified Sampling (Gemini only)")
    parser.add_argument("--fraud_count", type=int, default=500, help="Number of fraud dialogues")
    parser.add_argument("--normal_count", type=int, default=500, help="Number of normal dialogues")
    parser.add_argument("--api_key", required=True, help="Gemini API key")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--max_workers", type=int, default=3, help="Number of parallel workers")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests")
    parser.add_argument("--output_dir", default="optimized_dataset", help="Output directory")
    parser.add_argument("--use_stratified", action="store_true", default=True, 
                       help="Use stratified sampling for realistic user profiles")
    parser.add_argument("--demo_sampling", action="store_true",
                       help="Run sampling algorithm demo")
    
    args = parser.parse_args()
    
    # Demo sampling algorithm if requested
    if args.demo_sampling:
        from utils.stratified_sampling import demonstrate_stratified_sampling
        demonstrate_stratified_sampling()
        return
    
    # Tạo đường dẫn đầu ra
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Khởi tạo generator với Gemini
    generator = OptimizedDialogueGenerator(
        args.api_key, args.model, 
        args.max_workers, args.delay
    )
    
    # Tạo cuộc hội thoại lừa đảo
    if args.fraud_count > 0:
        print(f"🎯 Generating {args.fraud_count} fraud dialogues...")
        print(f"📊 Using {'Stratified Sampling' if args.use_stratified else 'Random Sampling'}")
        
        fraud_output = os.path.join(args.output_dir, f"fraud_dialogues_{timestamp}.jsonl")
        fraud_results = generator.generate_fraud_batch(
            args.fraud_count, fraud_output, args.use_stratified
        )
        print(f"✅ Fraud dialogues: {fraud_results['success_count']} success, {fraud_results['error_count']} errors")
    
    # Tạo cuộc hội thoại bình thường
    if args.normal_count > 0:
        print(f"📞 Generating {args.normal_count} normal dialogues...")
        normal_tasks = create_normal_tasks(args.normal_count)
        normal_output = os.path.join(args.output_dir, f"normal_dialogues_{timestamp}.jsonl")
        normal_results = generator.generate_batch(normal_tasks, normal_output)
        print(f"✅ Normal dialogues: {normal_results['success_count']} success, {normal_results['error_count']} errors")
    
    print(f"📁 All results saved to: {args.output_dir}")
    
    # Log sampling method used
    if args.fraud_count > 0:
        method = "Stratified Weighted Sampling" if args.use_stratified else "Random Sampling"
        print(f"🔬 Sampling method used: {method}")

if __name__ == "__main__":
    main()
