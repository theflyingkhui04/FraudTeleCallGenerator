# Cấu hình Gemini API
GEMINI_API_KEY = ""  # API key sẽ được truyền từ command line

# Cấu hình model - Gemini models
DEFAULT_MODEL = "gemini-2.0-flash"  # Model Gemini mặc định
FALLBACK_MODEL = "gemini-2.0-flash"  # Model dự phòng

# Cấu hình hội thoại
MAX_DIALOGUE_TURNS = 20
MAX_TOKENS_PER_MESSAGE = 500

# Danh sách các loại hội thoại bình thường
CONVERSATION_TYPES = [
    "Tư vấn dịch vụ",     # Tư vấn dịch vụ ngân hàng/viễn thông
    "Chăm sóc khách hàng", # Chăm sóc khách hàng chính thống
    "Hỗ trợ kỹ thuật",    # Hỗ trợ kỹ thuật IT/phần mềm
    "Tư vấn bán hàng",    # Tư vấn sản phẩm/dịch vụ
    "Hướng dẫn thủ tục",  # Hướng dẫn làm giấy tờ/thủ tục
    "Thông báo chính thức", # Thông báo từ cơ quan/tổ chức
    "Hẹn lịch",           # Hẹn lịch khám bệnh/họp/gặp mặt
    "Xác nhận thông tin", # Xác nhận đơn hàng/giao dịch
    "Giải đáp thắc mắc", # Giải đáp câu hỏi chung
    "Khảo sát ý kiến"     # Khảo sát/thu thập ý kiến
]

# Mức độ nhận thức an ninh mạng
AWARENESS_LEVELS = [
    "thấp",          # Ít kiến thức về lừa đảo, dễ tin tưởng
    "trung bình",    # Có kiến thức cơ bản nhưng vẫn có thể bị lừa
    "cao"            # Hiểu biết tốt về lừa đảo, cảnh giác cao
]

# Nghề nghiệp/Đối tượng thường bị nhắm mục tiêu
OCCUPATIONS = [
    "sinh viên",         # Sinh viên đại học/cao đẳng
    "nhân viên văn phòng", # Nhân viên công ty
    "người nghỉ hưu",    # Người cao tuổi nghỉ hưu
    "nội trợ",           # Nội trợ, chăm sóc gia đình
    "kinh doanh",        # Làm kinh doanh, buôn bán
    "giáo viên",         # Giáo viên/giảng viên
    "công nhân",         # Công nhân nhà máy
    "nông dân",          # Nông dân/làm nông nghiệp
    "tự do",             # Nghề tự do/freelancer
    "khác"               # Nghề nghiệp khác
]

# Cấu hình hồ sơ người dùng
USER_PROFILES = {
    "elderly": {
        "age": 70,
        "awareness": "low",
        "occupation": "retired"
    },
    "youth": {
        "age": 22,
        "awareness": "medium",
        "occupation": "student"
    },
    "professional": {
        "age": 40,
        "awareness": "high",
        "occupation": "engineer"
    }
}