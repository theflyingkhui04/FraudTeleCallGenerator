# Gemini API configuration - Default settings
GEMINI_API_KEY = ""  # API key sẽ được truyền từ command line

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

# Weighted occupation mapping based on fraud types for stratified sampling
FRAUD_OCCUPATION_WEIGHTS = {
    "Đầu tư": {
        "nhân viên văn phòng": 0.35,  # Quan tâm đầu tư, có thu nhập ổn định
        "kinh doanh": 0.30,           # Hiểu tài chính, tìm cơ hội đầu tư
        "sinh viên": 0.15,            # Dễ tin cơ hội kiếm tiền nhanh
        "tự do": 0.10,                # Thu nhập không ổn định, cần đầu tư
        "khác": 0.10
    },
    "Tình cảm": {
        "người nghỉ hưu": 0.30,       # Cô đơn, dễ tin tưởng
        "nội trợ": 0.25,              # Ít tiếp xúc xã hội, cần tình cảm
        "tự do": 0.20,                # Làm việc độc lập, ít gặp người
        "sinh viên": 0.15,            # Trẻ, dễ bị lôi kéo tình cảm
        "khác": 0.10
    },
    "Phishing": {
        "nhân viên văn phòng": 0.40,  # Thường dùng email, internet banking
        "sinh viên": 0.25,            # Dùng nhiều dịch vụ online
        "kinh doanh": 0.20,           # Giao dịch online thường xuyên
        "tự do": 0.10,                # Freelancer dùng nhiều platform
        "khác": 0.05
    },
    "Chiếm đoạt danh tính": {
        "người nghỉ hưu": 0.35,       # Ít hiểu công nghệ, dễ lộ thông tin
        "nội trợ": 0.25,              # Ít cảnh giác với thông tin cá nhân
        "nông dân": 0.20,             # Ít hiểu về bảo mật thông tin
        "công nhân": 0.15,            # Thu nhập thấp, ít quan tâm bảo mật
        "khác": 0.05
    },
    "Trúng thưởng": {
        "người nghỉ hưu": 0.30,       # Có thời gian, tin vào may mắn
        "nội trợ": 0.25,              # Muốn có thêm thu nhập cho gia đình
        "công nhân": 0.20,            # Thu nhập thấp, mong có thêm tiền
        "nông dân": 0.15,             # Tin vào vận may, ít hoài nghi
        "khác": 0.10
    },
    "Việc làm giả": {
        "sinh viên": 0.40,            # Tìm việc part-time, thiếu kinh nghiệm
        "nội trợ": 0.25,              # Muốn làm việc tại nhà
        "công nhân": 0.15,            # Tìm việc lương cao hơn
        "tự do": 0.15,                # Tìm thêm nguồn thu nhập
        "khác": 0.05
    },
    "Ngân hàng": {
        "nhân viên văn phòng": 0.35,  # Dùng nhiều dịch vụ ngân hàng
        "kinh doanh": 0.30,           # Giao dịch ngân hàng thường xuyên
        "người nghỉ hưu": 0.20,       # Có tiết kiệm, quan tâm bảo mật
        "sinh viên": 0.10,            # Mới tiếp xúc ngân hàng
        "khác": 0.05
    },
    "Giả danh công an": {
        "người nghỉ hưu": 0.30,       # Sợ pháp luật, dễ bị đe dọa
        "nông dân": 0.25,             # Ít hiểu luật, sợ cơ quan chức năng
        "nội trợ": 0.20,              # Lo lắng gia đình, dễ hoảng sợ
        "công nhân": 0.15,            # Sợ mất việc, vấn đề pháp lý
        "khác": 0.10
    },
    "Giả danh tổng đài": {
        "nhân viên văn phòng": 0.30,  # Thường liên hệ với dịch vụ khách hàng
        "sinh viên": 0.25,            # Sử dụng nhiều dịch vụ viễn thông
        "nội trợ": 0.20,              # Quản lý hóa đơn gia đình
        "người nghỉ hưu": 0.15,       # Tin tưởng đường dây nóng
        "khác": 0.10
    },
    "Lừa đảo bưu điện": {
        "người nghỉ hưu": 0.40,       # Thường nhận bưu phẩm, ít nghi ngờ
        "nội trợ": 0.25,              # Nhận hàng online cho gia đình
        "nông dân": 0.20,             # Ít tiếp xúc bưu điện, dễ tin
        "công nhân": 0.10,            # Ít sử dụng dịch vụ bưu chính
        "khác": 0.05
    },
    "Lừa đảo y tế": {
        "người nghỉ hưu": 0.45,       # Quan tâm sức khỏe, lo lắng bệnh tật
        "nội trợ": 0.25,              # Lo sức khỏe gia đình
        "nông dân": 0.15,             # Ít đi khám, sợ bệnh nặng
        "công nhân": 0.10,            # Lo về sức khỏe nghề nghiệp
        "khác": 0.05
    },
    "Lừa đảo học phí": {
        "sinh viên": 0.50,            # Trực tiếp liên quan học phí
        "nội trợ": 0.25,              # Lo học phí con em
        "nhân viên văn phòng": 0.15,  # Học thêm nâng cao trình độ
        "tự do": 0.05,                # Học skill mới
        "khác": 0.05
    },
    "Lừa đảo thuế": {
        "kinh doanh": 0.35,           # Phải nộp thuế, quan tâm hoàn thuế
        "nhân viên văn phòng": 0.30,  # Khai thuế thu nhập cá nhân
        "người nghỉ hưu": 0.20,       # Có thể được hoàn thuế
        "tự do": 0.10,                # Thu nhập không ổn định
        "khác": 0.05
    },
    "Lừa đảo từ thiện": {
        "người nghỉ hưu": 0.30,       # Có thời gian, tâm lý từ thiện
        "nội trợ": 0.25,              # Tâm lý mẹ, muốn giúp đỡ
        "giáo viên": 0.20,            # Có lòng nhân ái, giúp đỡ học sinh
        "nhân viên văn phòng": 0.15,  # Tham gia hoạt động xã hội
        "khác": 0.10
    },
    "Lừa đảo mua bán": {
        "sinh viên": 0.30,            # Mua sắm online nhiều, ít kinh nghiệm
        "nội trợ": 0.25,              # Mua sắm cho gia đình
        "nhân viên văn phòng": 0.20,  # Mua sắm tiện lợi online
        "tự do": 0.15,                # Thu nhập không ổn định, tìm hàng rẻ
        "khác": 0.10
    }
}

# Age ranges with weights for realistic distribution
AGE_RANGES_WEIGHTED = {
    "18-25": {
        "weight": 0.20,
        "occupations": ["sinh viên", "nhân viên văn phòng", "tự do", "khác"],
        "awareness_dist": {"thấp": 0.4, "trung bình": 0.5, "cao": 0.1}
    },
    "26-40": {
        "weight": 0.35,
        "occupations": ["nhân viên văn phòng", "kinh doanh", "giáo viên", "tự do", "khác"],
        "awareness_dist": {"thấp": 0.2, "trung bình": 0.6, "cao": 0.2}
    },
    "41-55": {
        "weight": 0.25,
        "occupations": ["kinh doanh", "giáo viên", "nhân viên văn phòng", "nội trợ", "khác"],
        "awareness_dist": {"thấp": 0.3, "trung bình": 0.5, "cao": 0.2}
    },
    "56-70": {
        "weight": 0.20,
        "occupations": ["người nghỉ hưu", "nội trợ", "nông dân", "khác"],
        "awareness_dist": {"thấp": 0.6, "trung bình": 0.3, "cao": 0.1}
    }
}

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