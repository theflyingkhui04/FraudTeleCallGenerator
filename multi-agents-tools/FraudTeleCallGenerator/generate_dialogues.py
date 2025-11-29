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

# Thực hiện P(o|f,a) với fraud weights và age compatibility để tránh "sinh viên 90 tuổi"
def _choose_occupation_with_weights(fraud_type: str, age_range: tuple) -> str:
    """Chọn nghề nghiệp theo P(o|f,a) - phụ thuộc cả fraud type và age range
    Tránh tình trạng vô lý như sinh viên 70 tuổi hay người nghỉ hưu 20 tuổi
    
    Args:
        fraud_type: Loại lừa đảo
        age_range: Tuple (min_age, max_age) 
    
    Returns:
        Nghề nghiệp phù hợp với cả fraud type và độ tuổi
    """
    # Lấy danh sách nghề phù hợp với độ tuổi trước
    age_range_key = f"{age_range[0]}-{age_range[1]}"
    age_appropriate_occs = config.AGE_RANGES_WEIGHTED.get(age_range_key, {}).get("occupations", config.OCCUPATIONS)
    
    # Lấy trọng số fraud-specific
    fraud_weights = config.FRAUD_OCCUPATION_WEIGHTS.get(fraud_type, {})
    
    if fraud_weights:
        # Kết hợp: chỉ lấy nghề vừa phù hợp tuổi VÀ có trong fraud weights
        combined_weights = {}
        for occ in age_appropriate_occs:
            if occ in fraud_weights:
                combined_weights[occ] = fraud_weights[occ]
        
        # Nếu có nghề phù hợp cả 2 tiêu chí thì dùng P(o|f,a)
        if combined_weights:
            occupations = list(combined_weights.keys())
            weights = list(combined_weights.values()) 
            return random.choices(occupations, weights=weights, k=1)[0]
    
    # Fallback: chọn random từ nghề phù hợp tuổi (ít nhất cũng logical)
    return random.choice(age_appropriate_occs)

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

# Cấu hình các giá trị theo chuẩn TeleAntiFraud gốc
AGE_RANGES = [
    (18, 25),  # Thanh niên
    (26, 40),  # Trung niên
    (41, 55),  # Trung cao tuổi
    (56, 70),  # Cao tuổi
]

FRAUD_TYPES = config.FRAUD_TYPES

OCCUPATIONS = config.OCCUPATIONS

AWARENESS_LEVELS = config.AWARENESS_LEVELS

def generate_dialogue(args, tts_id: str, user_age: int, user_awareness: str, fraud_type: str) -> Dict[str, Any]:
    """Sinh một hội thoại và trả về kết quả (theo chuẩn TeleAntiFraud gốc)"""
    try:
        # Ghi log tham số hội thoại
        logger.info(
            f"Bắt đầu sinh hội thoại {tts_id}: age={user_age}, awareness={user_awareness}, fraud_type={fraud_type}"
        )

        # Tạo agent bên trái (Kẻ lừa đảo)
        left_agent = LeftAgent(
            model=args.model,
            fraud_type=fraud_type,
            api_key=getattr(args, 'api_key', None)
        )

        # Tạo agent bên phải (Người dùng): chọn nghề theo P(o|f,a) 
        # Xác định age_range từ user_age cụ thể
        user_age_range = None
        for age_range in AGE_RANGES:
            if age_range[0] <= user_age <= age_range[1]:
                user_age_range = age_range
                break
        
        if user_age_range is None:
            # Fallback nếu user_age nằm ngoài ranges đã định nghĩa
            user_age_range = AGE_RANGES[0]  # Default to first range
            
        occupation = _choose_occupation_with_weights(fraud_type, user_age_range)

        right_agent = RightAgent(
            model=args.model,
            user_profile={
                "age": user_age,
                "awareness": user_awareness,
                "occupation": occupation
            },
            api_key=getattr(args, 'api_key', None)
        )

        # Tạo agent quản lý
        manager_agent = ManagerAgent(
            model=args.model,
            strictness="medium",
            api_key=getattr(args, 'api_key', None)
        )

        # Tạo bộ điều phối hội thoại
        conv_logger = ConversationLogger(console_output=False)
        orchestrator = DialogueOrchestrator(
            left_agent=left_agent,
            right_agent=right_agent,
            manager_agent=manager_agent,
            max_turns=args.max_turns,
            logger=conv_logger
        )

        # Sinh hội thoại
        dialogue_result = orchestrator.run_dialogue()

        # Ghi log lịch sử hội thoại
        logger.info(
            f"Hội thoại {tts_id} hoàn thành, tổng {len(dialogue_result['dialogue_history'])} lượt"
        )
        logger.info(f"Lịch sử hội thoại {tts_id}:")
        for msg in dialogue_result['dialogue_history']:
            role = "Kẻ lừa đảo" if msg['role'] == "left" else "Người dùng"
            logger.info(f"{role}: {msg['content']}")

        # Trích xuất lý do kết thúc
        termination_reason = (
            "Đạt tối đa lượt" if dialogue_result.get("reached_max_turns", False)
            else dialogue_result.get("termination_reason", "Không xác định")
        )
        # Nếu do quản lý kết thúc, rút ngắn lý do
        if dialogue_result.get("terminated_by_manager", False) and isinstance(termination_reason, str) and len(termination_reason) > 100:
            short_reason = termination_reason.split("。")[0] if "。" in termination_reason[:100] else termination_reason[:100]
            termination_reason = short_reason + "..."

        # Tách biệt nội dung hội thoại của hai bên
        left_messages: List[str] = []
        right_messages: List[str] = []
        for message in dialogue_result["dialogue_history"]:
            if message["role"] == "left":
                content = message["content"].replace('\n', ' ').strip()
                left_messages.append(content)
            elif message["role"] == "right":
                content = message["content"].replace('\n', ' ').strip()
                right_messages.append(content)

        # Tạo entry dữ liệu JSONL
        entry = {
            "tts_id": tts_id,
            "left": left_messages,
            "right": right_messages,
            "user_age": user_age,
            "user_awareness": user_awareness,
            "fraud_type": fraud_type,
            "occupation": occupation,
            "termination_reason": termination_reason,
            "terminator": dialogue_result.get("terminator", "natural")
        }

        # Lưu trữ hội thoại đầy đủ (tùy chọn)
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
    parser = argparse.ArgumentParser(description="Sinh dữ liệu hội thoại lừa đảo đa agent với Gemini")
    parser.add_argument("--count", type=int, default=20, help="Số lượng hội thoại cần sinh")
    parser.add_argument("--output", default="fraud_dialogues.jsonl", help="Đường dẫn file kết quả")
    parser.add_argument("--full_output_dir", default="full_dialogues", help="Thư mục lưu hội thoại đầy đủ")
    parser.add_argument("--save_full_dialogues", action="store_true", help="Luu file hoi thoai day du (debug)")
    parser.add_argument("--api_key", required=True, help="Gemini API key")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Tên model Gemini sử dụng")
    parser.add_argument("--max_turns", type=int, default=15, help="Số lượt hội thoại tối đa")
    parser.add_argument("--workers", type=int, default=10, help="Số luồng xử lý song song")
    args = parser.parse_args()
    
    # Ghi log thông tin khởi động
    logger.info(f"Bắt đầu sinh {args.count} hội thoại với Gemini model: {args.model}")
    
    # Cấu hình API key
    config.GEMINI_API_KEY = args.api_key
    config.DEFAULT_MODEL = args.model
    
    # Tạo thư mục lưu trữ kết quả nếu chưa tồn tại
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Tạo thư mục lưu trữ hội thoại đầy đủ (chỉ khi cần)
    if args.save_full_dialogues and not os.path.exists(args.full_output_dir):
        os.makedirs(args.full_output_dir)
    
    # Tạo danh sách nhiệm vụ
    tasks = []
    
    # Đảm bảo coverage đều theo tổ hợp (fraud_type, age_range, awareness) như TeleAntiFraud gốc
    combinations = []
    for age_range in AGE_RANGES:
        for awareness in AWARENESS_LEVELS:
            for fraud in FRAUD_TYPES:
                combinations.append((age_range, awareness, fraud))
    
    # Phân bổ số lượng nhiệm vụ cho mỗi tổ hợp tham số
    per_combination = args.count // len(combinations)
    remainder = args.count % len(combinations)
    
    # Thêm nhiệm vụ vào danh sách
    tts_counter = 1
    for combo in combinations:
        age_range, awareness, fraud = combo
        # Số lượng nhiệm vụ cho tổ hợp này
        combo_count = per_combination + (1 if remainder > 0 else 0)
        if remainder > 0:
            remainder -= 1
            
        for _ in range(combo_count):
            user_age = random.randint(age_range[0], age_range[1])
            tts_id = f"tts_fraud_{tts_counter:05d}"
            tasks.append((tts_id, user_age, awareness, fraud))
            tts_counter += 1    # Khởi tạo các biến thống kê và kết quả
    results = []
    success_count = 0
    error_count = 0
    age_stats = {}
    age_range_stats = {}
    awareness_stats = {}
    fraud_stats = {}
    terminator_stats = {}
    occupations_stats = {}
    
    # Xáo trộn thứ tự nhiệm vụ
    random.shuffle(tasks)
    
    # Sinh hội thoại song song
    logger.info(f"Bắt đầu sinh hội thoại song song, số luồng: {args.workers}")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Gửi tất cả nhiệm vụ vào xử lý
        future_to_task = {
            executor.submit(generate_dialogue, args, tts_id, user_age, awareness, fraud): 
            (tts_id, user_age, awareness, fraud) 
            for tts_id, user_age, awareness, fraud in tasks
        }
          # Xử lý kết quả trả về
        for future in tqdm(as_completed(future_to_task), total=len(tasks), desc="Sinh hội thoại"):
            task = future_to_task[future]
            try:
                result = future.result()
                if "error" not in result:
                    results.append(result)
                    success_count += 1
                    
                    # Cập nhật thống kê
                    age = result["user_age"]
                    awareness = result["user_awareness"] 
                    fraud = result["fraud_type"]
                    terminator = result["terminator"]
                    occupation = result["occupation"]

                    age_stats[age] = age_stats.get(age, 0) + 1
                    awareness_stats[awareness] = awareness_stats.get(awareness, 0) + 1
                    fraud_stats[fraud] = fraud_stats.get(fraud, 0) + 1
                    terminator_stats[terminator] = terminator_stats.get(terminator, 0) + 1
                    occupations_stats[occupation] = occupations_stats.get(occupation, 0) + 1
                    
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
    
    # Xuất thống kê phân phối
    stats_msg = f"\nThống kê tổng quan:"
    stats_msg += f"\n- Tổng hội thoại thành công: {success_count}"
    stats_msg += f"\n- Tổng hội thoại lỗi: {error_count}"
    stats_msg += f"\n- Tỷ lệ thành công: {success_count/(success_count+error_count)*100:.1f}%"
    stats_msg += f"\nPhân bố tuổi (tuổi cụ thể): {dict(sorted(age_stats.items()))}"
    # Age range order as tuples for readability
    age_range_counts = {}
    for age, count in age_stats.items():
        for i, (min_age, max_age) in enumerate(AGE_RANGES):
            if min_age <= age <= max_age:
                range_key = f"{min_age}-{max_age}"
                age_range_counts[range_key] = age_range_counts.get(range_key, 0) + count
                break
    stats_msg += f"\nPhân bố nhóm tuổi (range): {age_range_counts}"
    stats_msg += f"\nPhân bố nhận thức: {awareness_stats}"
    stats_msg += f"\nPhân bố loại lừa đảo: {fraud_stats}"
    stats_msg += f"\nPhân bố bên kết thúc: {terminator_stats}"
    stats_msg += f"\nPhân bố nghề nghiệp: {occupations_stats}"    
    try:
        print(stats_msg)
    except UnicodeEncodeError:
        print(stats_msg.encode('utf-8', errors='replace').decode('utf-8'))
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
