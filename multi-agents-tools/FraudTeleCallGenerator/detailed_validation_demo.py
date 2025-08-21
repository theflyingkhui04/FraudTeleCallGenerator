#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed Realism Score Calculation - Show step-by-step validation
"""

import sys
import os
import random
from collections import defaultdict

# Import paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

def detailed_realism_validation(profiles, method_name):
    """
    Chi tiết từng bước validation với logging
    """
    print(f"\n🔍 DETAILED VALIDATION: {method_name}")
    print("=" * 50)
    
    realistic_count = 0
    total_count = len(profiles)
    
    # Tracking rejection reasons
    rejection_reasons = defaultdict(int)
    
    for i, profile in enumerate(profiles):
        fraud_type = profile["fraud_type"]
        occupation = profile["occupation"] 
        age = profile["age"]
        awareness = profile["awareness"]
        
        is_realistic = True
        rejection_reason = None
        
        # ====== VALIDATION RULE 1: Age-Occupation Logic ======
        if occupation == "sinh viên" and age > 30:
            is_realistic = False
            rejection_reason = f"Age-Occupation: {age}-year-old student unrealistic"
            
        elif occupation == "người nghỉ hưu" and age < 50:
            is_realistic = False  
            rejection_reason = f"Age-Occupation: {age}-year-old retiree unrealistic"
            
        elif occupation == "nông dân" and age < 25:
            is_realistic = False
            rejection_reason = f"Age-Occupation: {age}-year-old farmer unlikely"
            
        # ====== VALIDATION RULE 2: Fraud-Occupation Targeting ======
        elif fraud_type in config.FRAUD_OCCUPATION_WEIGHTS:
            valid_occupations = list(config.FRAUD_OCCUPATION_WEIGHTS[fraud_type].keys())
            if occupation not in valid_occupations:
                is_realistic = False
                rejection_reason = f"Fraud-Occupation: {fraud_type} targeting {occupation} illogical"
        
        # ====== VALIDATION RULE 3: Awareness-Age Logic ======
        elif age > 60 and awareness == "cao":
            is_realistic = False
            rejection_reason = f"Awareness-Age: {age}-year-old with high tech awareness unusual"
            
        elif age < 25 and awareness == "thấp" and occupation in ["sinh viên", "tự do"]:
            is_realistic = False
            rejection_reason = f"Awareness-Occupation: Young {occupation} with low awareness unusual"
        
        # ====== RESULT LOGGING ======
        if is_realistic:
            realistic_count += 1
            status = "✅ PASS"
        else:
            rejection_reasons[rejection_reason] += 1
            status = "❌ FAIL"
        
        # Show first 10 profiles for debugging
        if i < 10:
            print(f"  Profile {i+1}: {status}")
            print(f"    {fraud_type} → {occupation} ({age} tuổi, {awareness} awareness)")
            if not is_realistic:
                print(f"    Reason: {rejection_reason}")
            print()
    
    # Summary statistics
    realism_score = realistic_count / total_count * 100
    print(f"📊 SUMMARY:")
    print(f"  Total Profiles: {total_count}")
    print(f"  Realistic Profiles: {realistic_count}")
    print(f"  Realism Score: {realism_score:.1f}%")
    
    # Rejection reason breakdown
    if rejection_reasons:
        print(f"\n❌ REJECTION BREAKDOWN:")
        for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = count / total_count * 100
            print(f"  {reason}: {count} ({pct:.1f}%)")
    
    return realism_score, rejection_reasons

def compare_validation_detailed():
    """So sánh chi tiết validation giữa Random vs Stratified"""
    
    print("🔬 DETAILED REALISM VALIDATION COMPARISON")
    print("=" * 60)
    
    # Generate sample profiles
    random.seed(42)  # Reproducible results
    
    # Random sampling profiles (simulate original approach)
    random_profiles = []
    fraud_types = config.FRAUD_TYPES
    occupations = config.OCCUPATIONS  
    awareness_levels = config.AWARENESS_LEVELS
    
    for i in range(50):  # Smaller sample for detailed analysis
        age = random.randint(18, 70)
        profile = {
            "fraud_type": random.choice(fraud_types),
            "occupation": random.choice(occupations),
            "age": age,
            "awareness": random.choice(awareness_levels),
            "method": "random"
        }
        random_profiles.append(profile)
    
    # Stratified sampling profiles (our approach)
    from utils.stratified_sampling import StratifiedSampler
    sampler = StratifiedSampler()
    
    # Create fraud distribution for 50 profiles
    fraud_distribution = {}
    base_count = 50 // len(fraud_types)
    remainder = 50 % len(fraud_types)
    
    for i, fraud_type in enumerate(fraud_types):
        fraud_distribution[fraud_type] = base_count + (1 if i < remainder else 0)
    
    stratified_user_profiles = sampler.generate_batch_profiles(fraud_distribution)
    stratified_profiles = []
    for profile in stratified_user_profiles:
        stratified_profiles.append({
            "fraud_type": profile["fraud_type"],
            "occupation": profile["occupation"], 
            "age": profile["age"],
            "awareness": profile["awareness"],
            "method": "stratified"
        })
    
    # Detailed validation
    random_score, random_rejections = detailed_realism_validation(random_profiles, "RANDOM SAMPLING")
    strat_score, strat_rejections = detailed_realism_validation(stratified_profiles, "STRATIFIED SAMPLING") 
    
    # Comparison summary
    print(f"\n🎯 COMPARISON RESULTS:")
    print("=" * 30)
    print(f"Random Sampling Score: {random_score:.1f}%")
    print(f"Stratified Sampling Score: {strat_score:.1f}%") 
    print(f"Improvement: +{strat_score - random_score:.1f} percentage points")
    
    print(f"\n💡 KEY INSIGHTS:")
    if strat_score > random_score:
        print(f"  ✅ Stratified sampling reduces logical inconsistencies")
        print(f"  🎯 Weighted selection creates realistic fraud-victim targeting")
        print(f"  📊 Age-occupation compatibility improves by {strat_score - random_score:.1f}%")
    
    # Show most common rejection reasons for random
    print(f"\n❌ MAIN ISSUES WITH RANDOM SAMPLING:")
    for reason, count in list(random_rejections.items())[:3]:
        print(f"  • {reason}: {count} cases")

if __name__ == "__main__":
    compare_validation_detailed()
