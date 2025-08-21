#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script để so sánh Random Sampling vs Stratified Sampling
Không cần API key - chỉ demo thuật toán sampling
"""

import sys
import os
import random
from collections import defaultdict, Counter

# Import paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from utils.stratified_sampling import StratifiedSampler

def demo_random_sampling(count: int = 100) -> list:
    """Demo random sampling (legacy method)"""
    print("🎲 RANDOM SAMPLING (Legacy Method)")
    print("=" * 40)
    
    profiles = []
    fraud_types = config.FRAUD_TYPES
    occupations = config.OCCUPATIONS
    awareness_levels = config.AWARENESS_LEVELS
    
    age_ranges = [(18, 30), (31, 45), (46, 60), (61, 75)]
    
    for i in range(count):
        age_range = random.choice(age_ranges)
        age = random.randint(age_range[0], age_range[1])
        
        profile = {
            "fraud_type": random.choice(fraud_types),
            "age": age,
            "occupation": random.choice(occupations),
            "awareness": random.choice(awareness_levels),
            "method": "random"
        }
        profiles.append(profile)
    
    return profiles

def demo_stratified_sampling(count: int = 100) -> list:
    """Demo stratified sampling (enhanced method)"""
    print("\n🎯 STRATIFIED SAMPLING (Enhanced Method)")
    print("=" * 40)
    
    sampler = StratifiedSampler()
    
    # Create balanced fraud distribution
    fraud_types = config.FRAUD_TYPES
    fraud_distribution = {}
    base_count = count // len(fraud_types)
    remainder = count % len(fraud_types)
    
    for i, fraud_type in enumerate(fraud_types):
        fraud_distribution[fraud_type] = base_count + (1 if i < remainder else 0)
    
    # Generate profiles
    user_profiles = sampler.generate_batch_profiles(fraud_distribution)
    
    # Convert to same format as random sampling
    profiles = []
    for profile in user_profiles:
        profiles.append({
            "fraud_type": profile["fraud_type"],
            "age": profile["age"], 
            "occupation": profile["occupation"],
            "awareness": profile["awareness"],
            "method": "stratified"
        })
    
    return profiles

def analyze_and_compare(random_profiles: list, stratified_profiles: list):
    """Phân tích và so sánh hai phương pháp sampling"""
    print("\n📊 SO SÁNH PHƯƠNG PHÁP SAMPLING")
    print("=" * 50)
    
    def analyze_profiles(profiles, method_name):
        print(f"\n🔍 {method_name.upper()}:")
        
        # Occupation distribution
        occupation_dist = Counter(p["occupation"] for p in profiles)
        print(f"  📋 Top 5 nghề nghiệp:")
        for occ, count in occupation_dist.most_common(5):
            pct = count / len(profiles) * 100
            print(f"    {occ}: {count} ({pct:.1f}%)")
        
        # Age distribution
        ages = [p["age"] for p in profiles]
        print(f"  👥 Tuổi: min={min(ages)}, max={max(ages)}, avg={sum(ages)/len(ages):.1f}")
        
        # Awareness distribution
        awareness_dist = Counter(p["awareness"] for p in profiles)
        print(f"  🧠 Awareness:")
        for level, count in awareness_dist.items():
            pct = count / len(profiles) * 100
            print(f"    {level}: {count} ({pct:.1f}%)")
        
        return occupation_dist, awareness_dist
    
    # Analyze both methods
    random_occ, random_aware = analyze_profiles(random_profiles, "Random Sampling")
    strat_occ, strat_aware = analyze_profiles(stratified_profiles, "Stratified Sampling")
    
    # Compare fraud-occupation alignment
    print(f"\n🎯 PHÂN TÍCH CHI TIẾT - FRAUD TYPE vs OCCUPATION:")
    print("-" * 50)
    
    def analyze_fraud_occupation_alignment(profiles, method_name):
        # Count fraud-occupation combinations
        fraud_occ_combinations = defaultdict(lambda: defaultdict(int))
        
        for profile in profiles:
            fraud_type = profile["fraud_type"]
            occupation = profile["occupation"]
            fraud_occ_combinations[fraud_type][occupation] += 1
        
        print(f"\n{method_name} - Top combinations:")
        
        # Show logical combinations for specific fraud types
        target_frauds = ["Đầu tư", "Việc làm giả", "Lừa đảo y tế", "Lừa đảo học phí"]
        
        for fraud_type in target_frauds:
            if fraud_type in fraud_occ_combinations:
                combinations = fraud_occ_combinations[fraud_type]
                total_for_fraud = sum(combinations.values())
                print(f"  {fraud_type} ({total_for_fraud} total):")
                
                # Sort by count and show top 3
                sorted_combs = sorted(combinations.items(), key=lambda x: x[1], reverse=True)
                for occ, count in sorted_combs[:3]:
                    pct = count / total_for_fraud * 100
                    print(f"    → {occ}: {count} ({pct:.1f}%)")
        
        return fraud_occ_combinations
    
    random_combs = analyze_fraud_occupation_alignment(random_profiles, "🎲 RANDOM")
    strat_combs = analyze_fraud_occupation_alignment(stratified_profiles, "🎯 STRATIFIED")
    
    # Calculate realism score
    print(f"\n📈 ĐIỂM CHẤT LƯỢNG (REALISM SCORE):")
    print("-" * 30)
    
    def calculate_realism_score(profiles):
        realistic_count = 0
        total_count = len(profiles)
        
        for profile in profiles:
            fraud_type = profile["fraud_type"]
            occupation = profile["occupation"]
            age = profile["age"]
            
            # Check logical combinations
            is_realistic = True
            
            # Age-occupation logic
            if occupation == "sinh viên" and age > 30:
                is_realistic = False
            elif occupation == "người nghỉ hưu" and age < 50:
                is_realistic = False
            elif occupation == "giáo viên" and age < 22:  # Cần tốt nghiệp đại học
                is_realistic = False
            
            # Fraud-occupation logic (based on config weights)
            if fraud_type in config.FRAUD_OCCUPATION_WEIGHTS:
                if occupation not in config.FRAUD_OCCUPATION_WEIGHTS[fraud_type]:
                    is_realistic = False
            
            if is_realistic:
                realistic_count += 1
        
        return realistic_count / total_count * 100
    
    random_score = calculate_realism_score(random_profiles)
    strat_score = calculate_realism_score(stratified_profiles)
    
    print(f"  🎲 Random Sampling: {random_score:.1f}%")
    print(f"  🎯 Stratified Sampling: {strat_score:.1f}%")
    print(f"  📊 Improvement: +{strat_score - random_score:.1f} percentage points")
    
    # Summary
    print(f"\n✨ TỔNG KẾT:")
    print("-" * 20)
    if strat_score > random_score:
        print(f"  ✅ Stratified Sampling tốt hơn Random Sampling")
        print(f"  🎯 Tạo ra user profiles realistic hơn {strat_score - random_score:.1f}%")
        print(f"  💡 Weighted occupation selection theo fraud type hiệu quả")
    else:
        print(f"  ⚠️  Cần tinh chỉnh thêm weighted mapping")

def main():
    print("🚀 DEMO SO SÁNH THUẬT TOÁN SAMPLING")
    print("Comparing Random vs Stratified Sampling for User Profile Generation")
    print("=" * 70)
    
    # Set seed for reproducible comparison
    random.seed(42)
    
    sample_size = 150
    print(f"📊 Sample size: {sample_size} profiles each method")
    
    # Generate samples
    random_profiles = demo_random_sampling(sample_size)
    stratified_profiles = demo_stratified_sampling(sample_size)
    
    # Analyze and compare
    analyze_and_compare(random_profiles, stratified_profiles)
    
    print(f"\n🎯 KẾT LUẬN:")
    print("Stratified Sampling với weighted occupation selection tạo ra")
    print("user profiles realistic và phù hợp với từng loại fraud hơn")
    print("so với random sampling truyền thống.")

if __name__ == "__main__":
    main()
