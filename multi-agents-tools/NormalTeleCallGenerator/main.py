import argparse
import json
from agents.left_agent import LeftAgent
from agents.right_agent import RightAgent
from agents.manager_agent import ManagerAgent
from logic.dialogue_orchestrator import DialogueOrchestrator
from utils.conversation_logger import ConversationLogger
import config

def main():
    # Phân tích các đối số dòng lệnh
    parser = argparse.ArgumentParser(description="Hệ thống sinh hội thoại bình thường đa agent")
    parser.add_argument("--conversation_type", default="Tư vấn dịch vụ", help="Loại tình huống hội thoại")
    parser.add_argument("--user_age", type=int, default=45, help="Tuổi người dùng")
    parser.add_argument("--awareness", default="trung bình", help="Phong cách giao tiếp: ngắn gọn, trung bình, chi tiết")
    parser.add_argument("--occupation", default="Giáo viên", help="Nghề nghiệp người dùng")
    parser.add_argument("--max_turns", type=int, default=20, help="Số lượt hội thoại tối đa")
    parser.add_argument("--output", default="dialogue_output.json", help="Đường dẫn file kết quả")
    parser.add_argument("--api_key", required=True, help="Gemini API key (bắt buộc)")
    parser.add_argument("--model", default='gemini-2.0-flash', help="Tên model Gemini")
    args = parser.parse_args()
    
    # Cập nhật config với Gemini
    if args.api_key:
        config.GEMINI_API_KEY = args.api_key
    if args.model:
        config.DEFAULT_MODEL = args.model
    
    # Khởi tạo trình ghi nhật ký
    logger = ConversationLogger()
    
    # Tạo các agent với Gemini API
    left_agent = LeftAgent(
        model=args.model,
        conversation_type=args.conversation_type,  # Sử dụng conversation_type thay vì fraud_type
        api_key=args.api_key
    )
    
    right_agent = RightAgent(
        model=args.model,
        user_profile={
            "age": args.user_age,
            "communication_style": args.awareness,  # Sử dụng awareness cho communication_style
            "occupation": args.occupation
        },
        api_key=args.api_key
    )
    
    manager_agent = ManagerAgent(
        model=args.model,
        strictness="medium",
        api_key=args.api_key
    )
    
    # Tạo một điều phối viên hội thoại
    orchestrator = DialogueOrchestrator(
        left_agent=left_agent,
        right_agent=right_agent,
        manager_agent=manager_agent,
        max_turns=args.max_turns,
        logger=logger
    )
    
    # Chạy cuộc trò chuyện
    result = orchestrator.run_dialogue()
    
    # Lưu kết quả
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Sinh hội thoại hoàn tất, tổng {len(result['dialogue_history'])} tin nhắn, đã lưu vào {args.output}")

if __name__ == "__main__":
    main()
