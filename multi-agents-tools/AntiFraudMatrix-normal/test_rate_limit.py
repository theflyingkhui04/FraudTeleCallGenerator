#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script sinh hội thoại với rate limiting tối ưu
"""

import time
import json
import argparse
from agents.left_agent import LeftAgent
from agents.right_agent import RightAgent
from agents.manager_agent import ManagerAgent
from logic.dialogue_orchestrator import DialogueOrchestrator
from utils.conversation_logger import ConversationLogger
import config

def main():
    parser = argparse.ArgumentParser(description="Test sinh hội thoại với rate limiting")
    parser.add_argument("--conversation_type", default="Tư vấn dịch vụ viễn thông", help="Loại hội thoại")
    parser.add_argument("--user_age", type=int, default=30, help="Tuổi người dùng")
    parser.add_argument("--awareness", default="trung bình", help="Phong cách giao tiếp")
    parser.add_argument("--occupation", default="công chức", help="Nghề nghiệp")
    parser.add_argument("--max_turns", type=int, default=5, help="Số lượt tối đa")
    parser.add_argument("--output", default="test_optimized.jsonl", help="File output")
    parser.add_argument("--api_key", required=True, help="Gemini API key")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Model name")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay giữa các lượt (seconds)")
    args = parser.parse_args()

    # Setup config với rate limiting
    config.OPENAI_API_KEY = args.api_key
    config.DEFAULT_MODEL = args.model
    
    print(f"🚀 Bắt đầu sinh hội thoại với delay {args.delay}s giữa các lượt...")
    
    # Tạo agents với retry delay cao hơn
    left_agent = LeftAgent(
        model=args.model,
        conversation_type=args.conversation_type,
        api_key=args.api_key,
        use_gemini=True,
        max_retries=3,
        retry_delay=args.delay
    )
    
    right_agent = RightAgent(
        model=args.model,
        user_profile={
            "age": args.user_age,
            "communication_style": args.awareness,
            "occupation": args.occupation
        },
        api_key=args.api_key,
        use_gemini=True,
        retry_delay=args.delay
    )
    
    manager_agent = ManagerAgent(
        model=args.model,
        strictness="medium",
        api_key=args.api_key,
        use_gemini=True,
        retry_delay=args.delay
    )
    
    logger = ConversationLogger()
    
    # Tạo orchestrator với delay giữa các lượt
    orchestrator = DialogueOrchestrator(
        left_agent=left_agent,
        right_agent=right_agent,
        manager_agent=manager_agent,
        max_turns=args.max_turns,
        logger=logger
    )
      # Custom run với rate limiting
    print("📞 Bắt đầu cuộc hội thoại...")
    
    dialogue_history = []
    
    # Sinh tin nhắn đầu tiên từ left agent
    print("⏳ Left agent sinh tin nhắn đầu tiên...")
    left_message = left_agent.generate_response()
    if not left_message:
        print("❌ Không thể sinh tin nhắn đầu tiên")
        return
    
    print(f"📤 Left: {left_message[:100]}...")
    dialogue_history.append({"role": "left", "content": left_message, "timestamp": time.time()})
    
    # Đợi trước khi tiếp tục
    time.sleep(args.delay)
    
    for turn in range(args.max_turns - 1):
        print(f"\n🔄 Lượt {turn + 2}/{args.max_turns}")
        
        # Right agent phản hồi
        print("⏳ Right agent đang phản hồi...")
        right_message = right_agent.generate_response(left_message)
        if not right_message:
            print("❌ Right agent không thể phản hồi")
            break
            
        print(f"📥 Right: {right_message[:100]}...")
        dialogue_history.append({"role": "right", "content": right_message, "timestamp": time.time()})
        
        # Đợi giữa các API call
        time.sleep(args.delay)
        
        # Manager đánh giá
        print("⏳ Manager đánh giá...")
        evaluation = manager_agent.evaluate_dialogue(dialogue_history)
        
        if evaluation.get("should_terminate", False):
            print(f"🏁 Hội thoại kết thúc: {evaluation.get('reason', 'Không rõ lý do')}")
            break
        
        # Đợi trước khi left tiếp tục
        time.sleep(args.delay)
        
        # Left agent tiếp tục
        print("⏳ Left agent tiếp tục...")
        left_message = left_agent.generate_response(right_message)
        if not left_message:
            print("❌ Left agent không thể tiếp tục")
            break
            
        print(f"📤 Left: {left_message[:100]}...")
        dialogue_history.append({"role": "left", "content": left_message, "timestamp": time.time()})
        
        # Đợi trước lượt tiếp theo
        time.sleep(args.delay)
    
    # Lưu kết quả
    result = {
        "dialogue_history": dialogue_history,
        "turns": len(dialogue_history),
        "completed": True
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Hoàn thành! Đã sinh {len(dialogue_history)} tin nhắn")
    print(f"📁 Kết quả lưu trong: {args.output}")

if __name__ == "__main__":
    main()
