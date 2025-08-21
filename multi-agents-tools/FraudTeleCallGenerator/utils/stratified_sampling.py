#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stratified Sampling Algorithm - Thuật toán lấy mẫu phân tầng cải tiến
Tạo user profile realistic dựa trên weighted occupation selection theo fraud type
"""

import random
import numpy as np
from typing import Dict, List, Any, Tuple
import sys
import os

# Import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class StratifiedSampler:
    """
    Stratified Sampling với weighted occupation selection
    Tạo user profile realistic hơn bằng cách:
    1. Chọn nghề nghiệp dựa trên trọng số theo fraud type
    2. Chọn độ tuổi phù hợp với nghề nghiệp
    3. Chọn awareness level dựa trên độ tuổi và nghề nghiệp
    """
    
    def __init__(self):
        self.fraud_occupation_weights = config.FRAUD_OCCUPATION_WEIGHTS
        self.age_ranges_weighted = config.AGE_RANGES_WEIGHTED
        self.occupations = config.OCCUPATIONS
        self.awareness_levels = config.AWARENESS_LEVELS
        
    def weighted_choice(self, choices: Dict[str, float]) -> str:
        """
        Chọn ngẫu nhiên có trọng số
        Args:
            choices: Dict mapping {item: weight}
        Returns:
            Selected item
        """
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights, k=1)[0]
    
    def get_weighted_occupation(self, fraud_type: str) -> str:
        """
        Chọn nghề nghiệp dựa trên trọng số theo fraud type
        Args:
            fraud_type: Loại lừa đảo
        Returns:
            Nghề nghiệp được chọn
        """
        if fraud_type in self.fraud_occupation_weights:
            return self.weighted_choice(self.fraud_occupation_weights[fraud_type])
        else:
            # Fallback to random choice if fraud_type not in weights
            return random.choice(self.occupations)
    
    def get_compatible_age_range(self, occupation: str) -> str:
        """
        Chọn độ tuổi phù hợp với nghề nghiệp
        Args:
            occupation: Nghề nghiệp
        Returns:
            Age range string
        """
        compatible_ranges = []
        
        for age_range, info in self.age_ranges_weighted.items():
            if occupation in info["occupations"]:
                compatible_ranges.append((age_range, info["weight"]))
        
        if compatible_ranges:
            # Weighted selection from compatible ranges
            ranges, weights = zip(*compatible_ranges)
            return random.choices(ranges, weights=weights, k=1)[0]
        else:
            # Fallback: chọn range phù hợp với nghề nghiệp
            if occupation == "sinh viên":
                return "18-25"
            elif occupation == "người nghỉ hưu":
                return "56-70"
            elif occupation in ["nội trợ", "nông dân"]:
                return random.choice(["41-55", "56-70"])
            else:
                return random.choice(["26-40", "41-55"])
    
    def get_age_from_range(self, age_range: str) -> int:
        """
        Lấy tuổi cụ thể từ age range
        Args:
            age_range: Age range string (e.g., "18-25")
        Returns:
            Specific age
        """
        range_mapping = {
            "18-25": (18, 25),
            "26-40": (26, 40),
            "41-55": (41, 55),
            "56-70": (56, 70)
        }
        
        if age_range in range_mapping:
            min_age, max_age = range_mapping[age_range]
            return random.randint(min_age, max_age)
        else:
            return random.randint(18, 70)  # Fallback
    
    def get_awareness_for_age_occupation(self, age_range: str, occupation: str) -> str:
        """
        Chọn awareness level dựa trên độ tuổi và nghề nghiệp
        Args:
            age_range: Age range
            occupation: Nghề nghiệp
        Returns:
            Awareness level
        """
        # Base distribution from age
        if age_range in self.age_ranges_weighted:
            base_dist = self.age_ranges_weighted[age_range]["awareness_dist"]
        else:
            base_dist = {"thấp": 0.33, "trung bình": 0.34, "cao": 0.33}
        
        # Adjust based on occupation
        adjusted_dist = base_dist.copy()
        
        # Nghề nghiệp có hiểu biết cao về công nghệ/bảo mật
        if occupation in ["nhân viên văn phòng", "giáo viên", "tự do"]:
            adjusted_dist["cao"] = min(adjusted_dist["cao"] * 1.5, 0.8)
            adjusted_dist["thấp"] = max(adjusted_dist["thấp"] * 0.7, 0.1)
            
        # Nghề nghiệp ít tiếp xúc công nghệ
        elif occupation in ["nông dân", "công nhân", "người nghỉ hưu"]:
            adjusted_dist["thấp"] = min(adjusted_dist["thấp"] * 1.3, 0.8)
            adjusted_dist["cao"] = max(adjusted_dist["cao"] * 0.6, 0.05)
        
        # Normalize weights
        total = sum(adjusted_dist.values())
        for key in adjusted_dist:
            adjusted_dist[key] /= total
            
        return self.weighted_choice(adjusted_dist)
    
    def generate_stratified_profile(self, fraud_type: str) -> Dict[str, Any]:
        """
        Tạo user profile stratified hoàn chỉnh
        Args:
            fraud_type: Loại lừa đảo
        Returns:
            User profile dict
        """
        # 1. Chọn nghề nghiệp theo trọng số fraud type
        occupation = self.get_weighted_occupation(fraud_type)
        
        # 2. Chọn độ tuổi phù hợp với nghề nghiệp
        age_range = self.get_compatible_age_range(occupation)
        age = self.get_age_from_range(age_range)
        
        # 3. Chọn awareness dựa trên tuổi và nghề nghiệp
        awareness = self.get_awareness_for_age_occupation(age_range, occupation)
        
        return {
            "age": age,
            "age_range": age_range,
            "occupation": occupation,
            "awareness": awareness,
            "fraud_type": fraud_type
        }
    
    def generate_batch_profiles(self, fraud_distribution: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Tạo batch user profiles với phân phối fraud types
        Args:
            fraud_distribution: Dict {fraud_type: count}
        Returns:
            List of user profiles
        """
        profiles = []
        
        for fraud_type, count in fraud_distribution.items():
            for _ in range(count):
                profile = self.generate_stratified_profile(fraud_type)
                profiles.append(profile)
        
        # Shuffle để tránh bias trong thứ tự
        random.shuffle(profiles)
        return profiles
    
    def analyze_profile_distribution(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phân tích phân phối các profiles đã tạo
        Args:
            profiles: List of user profiles
        Returns:
            Distribution statistics
        """
        stats = {
            "total_profiles": len(profiles),
            "fraud_type_dist": {},
            "occupation_dist": {},
            "age_range_dist": {},
            "awareness_dist": {},
            "cross_tabulation": {}
        }
        
        # Count distributions
        for profile in profiles:
            fraud_type = profile["fraud_type"]
            occupation = profile["occupation"]
            age_range = profile["age_range"]
            awareness = profile["awareness"]
            
            # Basic distributions
            stats["fraud_type_dist"][fraud_type] = stats["fraud_type_dist"].get(fraud_type, 0) + 1
            stats["occupation_dist"][occupation] = stats["occupation_dist"].get(occupation, 0) + 1
            stats["age_range_dist"][age_range] = stats["age_range_dist"].get(age_range, 0) + 1
            stats["awareness_dist"][awareness] = stats["awareness_dist"].get(awareness, 0) + 1
            
            # Cross tabulation: fraud_type vs occupation
            key = f"{fraud_type}_{occupation}"
            stats["cross_tabulation"][key] = stats["cross_tabulation"].get(key, 0) + 1
        
        # Convert to percentages
        total = len(profiles)
        for dist_name in ["fraud_type_dist", "occupation_dist", "age_range_dist", "awareness_dist"]:
            for key in stats[dist_name]:
                count = stats[dist_name][key]
                stats[dist_name][key] = {
                    "count": count,
                    "percentage": round(count / total * 100, 2)
                }
        
        return stats
    
    def validate_sampling_quality(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Đánh giá chất lượng sampling
        Args:
            profiles: List of user profiles
        Returns:
            Quality metrics
        """
        quality_metrics = {
            "realistic_combinations": 0,
            "total_profiles": len(profiles),
            "quality_score": 0.0,
            "issues": []
        }
        
        for profile in profiles:
            is_realistic = True
            
            # Check age-occupation compatibility
            age = profile["age"]
            occupation = profile["occupation"]
            
            if occupation == "sinh viên" and age > 30:
                is_realistic = False
                quality_metrics["issues"].append(f"Sinh viên {age} tuổi không realistic")
            
            if occupation == "người nghỉ hưu" and age < 50:
                is_realistic = False
                quality_metrics["issues"].append(f"Người nghỉ hưu {age} tuổi không realistic")
            
            # Check fraud-occupation logic
            fraud_type = profile["fraud_type"]
            if fraud_type in self.fraud_occupation_weights:
                expected_occupations = list(self.fraud_occupation_weights[fraud_type].keys())
                if occupation not in expected_occupations:
                    is_realistic = False
                    quality_metrics["issues"].append(
                        f"Fraud {fraud_type} với occupation {occupation} ít phù hợp"
                    )
            
            if is_realistic:
                quality_metrics["realistic_combinations"] += 1
        
        quality_metrics["quality_score"] = (
            quality_metrics["realistic_combinations"] / quality_metrics["total_profiles"] * 100
        )
        
        return quality_metrics


def demonstrate_stratified_sampling():
    """Demo function để test stratified sampling"""
    print("🔬 DEMO: Stratified Sampling Algorithm")
    print("=" * 50)
    
    sampler = StratifiedSampler()
    
    # Test fraud distribution
    fraud_distribution = {
        "Đầu tư": 20,
        "Tình cảm": 15,
        "Phishing": 15,
        "Việc làm giả": 20,
        "Lừa đảo y tế": 15,
        "Lừa đảo học phí": 15
    }
    
    print(f"📊 Generating {sum(fraud_distribution.values())} profiles...")
    profiles = sampler.generate_batch_profiles(fraud_distribution)
    
    print(f"✅ Generated {len(profiles)} profiles")
    
    # Analyze distribution
    print("\n📈 PHÂN TÍCH PHÂN PHỐI:")
    stats = sampler.analyze_profile_distribution(profiles)
    
    print(f"📋 Tổng profiles: {stats['total_profiles']}")
    
    print("\n🎯 Phân phối nghề nghiệp:")
    for occupation, data in stats["occupation_dist"].items():
        print(f"  {occupation}: {data['count']} ({data['percentage']}%)")
    
    print("\n👥 Phân phối độ tuổi:")
    for age_range, data in stats["age_range_dist"].items():
        print(f"  {age_range}: {data['count']} ({data['percentage']}%)")
    
    print("\n🧠 Phân phối awareness:")
    for awareness, data in stats["awareness_dist"].items():
        print(f"  {awareness}: {data['count']} ({data['percentage']}%)")
    
    # Quality validation
    print("\n🔍 ĐÁNH GIÁ CHẤT LƯỢNG:")
    quality = sampler.validate_sampling_quality(profiles)
    print(f"✅ Realistic combinations: {quality['realistic_combinations']}/{quality['total_profiles']}")
    print(f"📊 Quality Score: {quality['quality_score']:.1f}%")
    
    if quality["issues"]:
        print(f"⚠️  Issues found: {len(quality['issues'])}")
        for issue in quality["issues"][:5]:  # Show first 5 issues
            print(f"   - {issue}")
    
    # Show some example profiles
    print("\n📝 VÍ DỤ PROFILES:")
    for i, profile in enumerate(profiles[:5]):
        print(f"  {i+1}. {profile['fraud_type']} -> {profile['occupation']} "
              f"({profile['age']} tuổi, awareness: {profile['awareness']})")


if __name__ == "__main__":
    demonstrate_stratified_sampling()
