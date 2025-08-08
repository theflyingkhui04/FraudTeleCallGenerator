# Gemini API configuration - Default settings
OPENAI_API_KEY = ""  # API key sẽ được truyền từ command line
OPENAI_BASE_URL = ""  # Không cần base_url cho Gemini

# Model configuration - Gemini models
DEFAULT_MODEL = "gemini-2.0-flash"  # Model Gemini mặc định
FALLBACK_MODEL = "gemini-2.0-flash"  # Backup model

# Conversation configuration
MAX_DIALOGUE_TURNS = 20
MAX_TOKENS_PER_MESSAGE = 500

# Loại lừa đảo - cập nhật các kịch bản thực tế ở Việt Nam
FRAUD_TYPES = [
    "Đầu tư",                          # Lừa đảo đầu tư tài chính, crypto, forex
    "Tình cảm",                        # Lừa đảo tình cảm, kết bạn online
    "Phishing",                        # Lừa đảo phishing, fake website
    "Chiếm đoạt danh tính",           # Chiếm đoạt thông tin cá nhân
    "Trúng thưởng",                    # Lừa đảo trúng thưởng, quay số may mắn
    "Việc làm giả",                    # Lừa đảo việc nhẹ lương cao, làm online
    "Ngân hàng",                       # Lừa đảo ngân hàng, thẻ ATM
    "Giả danh công an",                # Giả danh công an/viện kiểm sát/tòa án
    "Giả danh tổng đài",              # Giả danh nhân viên ngân hàng/viễn thông
    "Lừa đảo bưu điện",               # Giả danh bưu điện có bưu phẩm/tiền
    "Lừa đảo y tế",                   # Giả danh bệnh viện/bác sĩ/bảo hiểm y tế
    "Lừa đảo học phí",                # Giả danh trường học/học bổng/khóa học
    "Lừa đảo thuế",                   # Giả danh cơ quan thuế hoàn thuế
    "Lừa đảo từ thiện",               # Kêu gọi từ thiện giả, quyên góp
    "Lừa đảo mua bán",                # Lừa đảo mua bán online, ship COD giả
]

# Mapping fraud_type tiếng Anh <-> tiếng Việt để hỗ trợ người dùng
FRAUD_TYPE_MAPPING = {
    # Tiếng Việt -> Tiếng Anh (cho hệ thống xử lý)
    "Đầu tư": "investment",
    "Tình cảm": "romance", 
    "Phishing": "phishing",
    "Chiếm đoạt danh tính": "identity_theft",
    "Trúng thưởng": "lottery",
    "Việc làm giả": "fake_job",
    "Ngân hàng": "banking",
    "Giả danh công an": "impersonation_police",
    "Giả danh tổng đài": "impersonation_call_center",
    "Lừa đảo bưu điện": "postal_scam",
    "Lừa đảo y tế": "medical_scam",
    "Lừa đảo học phí": "education_scam",
    "Lừa đảo thuế": "tax_scam",
    "Lừa đảo từ thiện": "charity_scam",
    "Lừa đảo mua bán": "ecommerce_scam",
    
    # Tiếng Anh -> Tiếng Việt (cho hiển thị)
    "investment": "Đầu tư",
    "romance": "Tình cảm",
    "phishing": "Phishing",
    "identity_theft": "Chiếm đoạt danh tính",
    "lottery": "Trúng thưởng",
    "fake_job": "Việc làm giả",
    "banking": "Ngân hàng",
    "impersonation_police": "Giả danh công an",
    "impersonation_call_center": "Giả danh tổng đài",
    "postal_scam": "Lừa đảo bưu điện",
    "medical_scam": "Lừa đảo y tế",
    "education_scam": "Lừa đảo học phí",
    "tax_scam": "Lừa đảo thuế",
    "charity_scam": "Lừa đảo từ thiện",
    "ecommerce_scam": "Lừa đảo mua bán"
}

# Mô tả chi tiết từng loại lừa đảo
FRAUD_TYPE_DESCRIPTIONS = {
    "Đầu tư": "Lừa đảo đầu tư tài chính, crypto, forex, chứng khoán với lời hứa lợi nhuận cao",
    "Tình cảm": "Lừa đảo tình cảm, kết bạn online, tạo lập mối quan hệ rồi xin tiền",
    "Phishing": "Lừa đảo qua email, SMS, website giả để đánh cắp thông tin đăng nhập",
    "Chiếm đoạt danh tính": "Thu thập thông tin cá nhân (CMND, số thẻ) để mạo danh",
    "Trúng thưởng": "Thông báo giả về việc trúng thưởng để lừa đóng phí thuế",
    "Việc làm giả": "Quảng cáo việc nhẹ lương cao, yêu cầu đóng phí đào tạo",
    "Ngân hàng": "Giả danh ngân hàng để lấy thông tin thẻ, mã PIN, OTP",
    "Giả danh công an": "Mạo danh công an/viện kiểm sát để đe dọa và tống tiền",
    "Giả danh tổng đài": "Giả danh tổng đài chăm sóc khách hàng để lấy thông tin",
    "Lừa đảo bưu điện": "Giả danh bưu điện báo có bưu phẩm cần đóng phí",
    "Lừa đảo y tế": "Giả danh bệnh viện/bác sĩ để lừa tiền điều trị hoặc bảo hiểm",
    "Lừa đảo học phí": "Giả danh trường học về học bổng hoặc đóng học phí",
    "Lừa đảo thuế": "Giả danh cơ quan thuế về hoàn thuế hoặc phạt thuế",
    "Lừa đảo từ thiện": "Kêu gọi quyên góp giả cho các hoàn cảnh khó khăn",
    "Lừa đảo mua bán": "Lừa đảo trong giao dịch mua bán online, ship COD giả"
}

# Thông tin người dùng mẫu để kiểm tra
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

# Loại hội thoại (cho hệ thống bình thường)
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