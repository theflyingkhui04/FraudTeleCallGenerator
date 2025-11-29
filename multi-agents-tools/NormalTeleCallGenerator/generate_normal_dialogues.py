import os
import json
import random
import argparse
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Dict, List, Any

from agents.left_agent import LeftAgent
from agents.right_agent import RightAgent
from agents.manager_agent import ManagerAgent
from logic.dialogue_orchestrator import DialogueOrchestrator
from utils.conversation_logger import ConversationLogger
import config

# Cấu hình ghi log toàn cục với UTF-8 cho Windows
import sys

# Tạo file handler với UTF-8 encoding
file_handler = logging.FileHandler('run.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                          datefmt='%Y-%m-%d %H:%M:%S'))

# Tạo stream handler với UTF-8 cho console (Windows safe)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                            datefmt='%Y-%m-%d %H:%M:%S'))

# Cấu hình root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler],
    force=True
)
logger = logging.getLogger(__name__)

# Cấu hình tham số với stratified sampling cho normal calls
AGE_RANGES = [
    (18, 25),  # Thanh niên
    (26, 40),  # Trung niên
    (41, 55),  # Trung cao tuổi
    (56, 70),  # Cao tuổi
]

AWARENESS_LEVELS = config.AWARENESS_LEVELS
CONVERSATION_TYPES = config.CONVERSATION_TYPES  
OCCUPATIONS = config.OCCUPATIONS

def _choose_occupation_by_age(age_range):
    """
    Chọn nghề nghiệp chỉ dựa vào độ tuổi P(o|a) cho normal calls.
    Conversation type không ảnh hưởng đến occupation choice.
    
    Args:
        age_range: Tuple (min_age, max_age)
    
    Returns:
        Nghề nghiệp phù hợp với độ tuổi
    """
    # Age-occupation mapping for realistic combinations
    age_mapping = {
        (18, 25): ["sinh viên", "nhân viên văn phòng", "tự do", "khác"],
        (26, 40): ["nhân viên văn phòng", "kinh doanh", "giáo viên", "tự do", "khác"],  
        (41, 55): ["kinh doanh", "giáo viên", "nhân viên văn phòng", "nội trợ", "khác"],
        (56, 70): ["người nghỉ hưu", "nội trợ", "nông dân", "khác"]
    }
    
    age_appropriate_occs = age_mapping.get(age_range, OCCUPATIONS)
    return random.choice(age_appropriate_occs)

def generate_dialogue(args, tts_id: str, user_age: int, user_awareness: str, conversation_type: str) -> Dict[str, Any]:
    """Sinh một hội thoại và trả về kết quả (với P(o|a) cho normal calls)"""
    try:
        # Ghi log tham số hội thoại
        logger.info(f"Bắt đầu sinh hội thoại {tts_id}: age={user_age}, awareness={user_awareness}, conversation_type={conversation_type}")
        
        # Tạo agent
        left_agent = LeftAgent(
            model=args.model,
            conversation_type=conversation_type,
            api_key=args.api_key
        )
        
        # Chọn nghề nghiệp theo P(o|a) - chỉ phụ thuộc vào tuổi
        # Xác định age_range từ user_age cụ thể
        user_age_range = None
        for age_range in AGE_RANGES:
            if age_range[0] <= user_age <= age_range[1]:
                user_age_range = age_range
                break
        
        if user_age_range is None:
            # Fallback nếu user_age nằm ngoài ranges đã định nghĩa  
            user_age_range = AGE_RANGES[0]  # Default to first range
            
        occupation = _choose_occupation_by_age(user_age_range)
        
        right_agent = RightAgent(
            model=args.model,
            user_profile={
                "age": user_age,
                "communication_style": "medium",  # Default communication style
                "occupation": occupation
            },
            api_key=args.api_key
        )
        
        manager_agent = ManagerAgent(
            model=args.model,
            strictness="medium",
            api_key=args.api_key
        )
        
        # Tạo dialogue orchestrator, tắt console output
        conv_logger = ConversationLogger(console_output=False)
        orchestrator = DialogueOrchestrator(
            left_agent=left_agent,
            right_agent=right_agent,
            manager_agent=manager_agent,
            max_turns=args.max_turns,
            logger=conv_logger
        )
        
        # Chạy hội thoại
        dialogue_result = orchestrator.run_dialogue()
        
        # Ghi log lịch sử hội thoại
        logger.info(f"Hội thoại {tts_id} hoàn thành, tổng {len(dialogue_result['dialogue_history'])} lượt")
        logger.info(f"Lịch sử hội thoại {tts_id}:")
        for msg in dialogue_result['dialogue_history']:
            role = "Nhân viên dịch vụ" if msg['role'] == "left" else "Khách hàng"
            logger.info(f"{role}: {msg['content']}")
        
        # Trích xuất lý do kết thúc
        termination_reason = "Đạt số lượt tối đa" if dialogue_result.get("reached_max_turns", False) else dialogue_result.get("termination_reason", "Không rõ")
        # Nếu manager kết thúc, rút gọn lý do nếu quá dài
        if dialogue_result.get("terminated_by_manager", False) and isinstance(termination_reason, str) and len(termination_reason) > 100:
            short_reason = termination_reason.split(".")[0] if "." in termination_reason[:100] else termination_reason[:100]
            termination_reason = short_reason + "..."
        
        # Trích xuất nội dung hội thoại
        left_messages = []
        right_messages = []
        
        for message in dialogue_result["dialogue_history"]:
            if message["role"] == "left":
                left_messages.append(message["content"])
            elif message["role"] == "right":
                right_messages.append(message["content"])
        
        # Tạo entry dữ liệu JSONL
        entry = {
            "tts_id": tts_id,
            "left": left_messages,
            "right": right_messages,
            "user_age": user_age,
            "user_awareness": user_awareness,
            "conversation_type": conversation_type,
            "occupation": occupation,
            "termination_reason": termination_reason,
            "terminator": dialogue_result.get("terminator", "natural")
        }
        
        # Lưu hội thoại đầy đủ (tùy chọn)
        if args.save_full_dialogues:
            full_dialogue_path = os.path.join(args.full_output_dir, f"{tts_id}.json")
            with open(full_dialogue_path, 'w', encoding='utf-8') as f:
                json.dump(dialogue_result, f, ensure_ascii=False, indent=2)
            logger.info(f"Hội thoại {tts_id} xử lý xong, lý do kết thúc: {termination_reason}")
            logger.info(f"Đã lưu hội thoại đầy đủ vào {full_dialogue_path}")
        else:
            logger.info(f"Hội thoại {tts_id} xử lý xong, lý do kết thúc: {termination_reason}")
        
        return entry
    
    except Exception as e:
        logger.error(f"Lỗi khi sinh hội thoại {tts_id}: {e}", exc_info=True)
        return {"error": str(e), "tts_id": tts_id}

def main():
    # Phân tích tham số dòng lệnh
    parser = argparse.ArgumentParser(description="Sinh dữ liệu hội thoại bình thường đa agent")
    parser.add_argument("--count", type=int, default=20, help="Số lượng hội thoại cần sinh")
    parser.add_argument("--output", default="normal_dialogues.jsonl", help="Đường dẫn file kết quả")
    parser.add_argument("--full_output_dir", default="full_normal_dialogues", help="Thư mục lưu hội thoại đầy đủ")
    parser.add_argument("--save_full_dialogues", action="store_true", help="Luu file hoi thoai day du (debug)")
    parser.add_argument("--api_key", required=True, help="Gemini API key")
    parser.add_argument("--model", required=True, help="Tên model Gemini sử dụng")
    parser.add_argument("--max_turns", type=int, default=15, help="Số lượt hội thoại tối đa")
    parser.add_argument("--workers", type=int, default=10, help="Số luồng xử lý song song")
    args = parser.parse_args()
    # Ghi log thông tin khởi động
    logger.info(f"Bắt đầu sinh {args.count} hội thoại bình thường với Gemini model: {args.model}")
    
    # Cấu hình API key
    config.GEMINI_API_KEY = args.api_key
    config.DEFAULT_MODEL = args.model
    
    # Tạo thư mục output
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Tạo thư mục lưu hội thoại đầy đủ (chỉ khi cần)
    if args.save_full_dialogues and not os.path.exists(args.full_output_dir):
        os.makedirs(args.full_output_dir)
    
    # Chuẩn bị danh sách nhiệm vụ theo stratified sampling (c,a,w) + P(o|a)
    tasks = []
    
    # Tạo tất cả combinations (conversation_type, age_range, awareness) 
    # Khác với fraud generation: conversation_type không ảnh hưởng occupation choice
    combinations = []
    for conv_type in CONVERSATION_TYPES:
        for age_range in AGE_RANGES:  
            for awareness in AWARENESS_LEVELS:
                combinations.append((conv_type, age_range, awareness))
    
    logger.info(f"Total combinations (c,a,w): {len(CONVERSATION_TYPES)} × {len(AGE_RANGES)} × {len(AWARENESS_LEVELS)} = {len(combinations)}")
    
    # Phân bổ số lượng cho mỗi combination
    per_combination = args.count // len(combinations)
    remainder = args.count % len(combinations)
    
    logger.info(f"Base quota per combination: {per_combination}, remainder: {remainder}")
    
    # Thêm nhiệm vụ với stratified distribution
    tts_counter = 1
    for i, combo in enumerate(combinations):
        conv_type, age_range, awareness = combo
        # Số lượng cho combination này
        combo_count = per_combination + (1 if remainder > 0 else 0)
        if remainder > 0:
            remainder -= 1
            
        for _ in range(combo_count):
            user_age = random.randint(age_range[0], age_range[1])
            tts_id = f"tts_normal_{tts_counter:05d}"
            # Note: occupation sẽ được chọn trong generate_dialogue() theo P(o|a)
            tasks.append((tts_id, user_age, awareness, conv_type))
            tts_counter += 1
    
    # Random hóa thứ tự nhiệm vụ
    random.shuffle(tasks)
    
    # Sinh hội thoại song song
    results = []
    success_count = 0
    error_count = 0
    
    logger.info(f"Bắt đầu sinh hội thoại song song, số luồng: {args.workers}")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit tất cả nhiệm vụ
        future_to_task = {
            executor.submit(generate_dialogue, args, tts_id, user_age, awareness, conv_type): 
            (tts_id, user_age, awareness, conv_type) 
            for tts_id, user_age, awareness, conv_type in tasks
        }
        
        # Xử lý nhiệm vụ hoàn thành
        for future in tqdm(as_completed(future_to_task), total=len(tasks), desc="Sinh hội thoại"):
            task = future_to_task[future]
            try:
                result = future.result()
                if "error" not in result:
                    results.append(result)
                    success_count += 1
                else:
                    logger.error(f"Nhiệm vụ {task[0]} thất bại: {result['error']}")
                    error_count += 1
            except Exception as e:
                logger.error(f"Lỗi khi xử lý nhiệm vụ {task[0]}: {e}", exc_info=True)
                error_count += 1
    
    # Ghi kết quả vào file JSONL
    with open(args.output, 'w', encoding='utf-8') as f:
        for entry in results:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # Xuất thống kê
    completion_msg = f"Hoàn thành! Đã sinh {len(results)} hội thoại, thành công: {success_count}, thất bại: {error_count}, đã lưu vào {args.output}"
    print(completion_msg)
    logger.info(completion_msg)
    
    # Thống kê phân phối
    age_stats = {"18-25": 0, "26-40": 0, "41-55": 0, "56-70": 0}
    awareness_stats = {"thấp": 0, "trung bình": 0, "cao": 0}
    conversation_stats = {conv_type: 0 for conv_type in CONVERSATION_TYPES}
    terminator_stats = {"left": 0, "right": 0, "natural": 0}
    occupations_stats = {occupation: 0 for occupation in OCCUPATIONS}
    
    for entry in results:
        age = entry["user_age"]
        if 18 <= age <= 25:
            age_stats["18-25"] += 1
        elif 26 <= age <= 40:
            age_stats["26-40"] += 1
        elif 41 <= age <= 55:
            age_stats["41-55"] += 1
        elif 56 <= age <= 70:
            age_stats["56-70"] += 1
            
        awareness_stats[entry["user_awareness"]] += 1
        conversation_stats[entry["conversation_type"]] += 1
        occupations_stats[entry["occupation"]] += 1
        
        # Thống kê bên kết thúc
        terminator = entry.get("terminator", "natural")
        if terminator in terminator_stats:
            terminator_stats[terminator] += 1
    
    # In thống kê phân phối
    stats_msg = "\nThống kê phân phối:"
    stats_msg += f"\nPhân bố độ tuổi: {age_stats}"
    stats_msg += f"\nPhân bố mức độ cảnh giác: {awareness_stats}"
    stats_msg += f"\nPhân bố loại hội thoại: {conversation_stats}"
    stats_msg += f"\nPhân bố bên kết thúc: {terminator_stats}"
    stats_msg += f"\nPhân bố nghề nghiệp: {occupations_stats}"
    
    print(stats_msg)
    logger.info(stats_msg)
    
if __name__ == "__main__":
    start_time = time.time()
    try:
        main()
    except Exception as e:
        logger.critical("Lỗi nghiêm trọng trong quá trình chạy chương trình", exc_info=True)
    
    elapsed = time.time() - start_time
    logger.info(f"Tổng thời gian: {elapsed:.2f} giây")
    print(f"Tổng thời gian: {elapsed:.2f} giây")
