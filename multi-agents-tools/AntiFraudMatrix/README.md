# Hệ thống tạo đối thoại gian lận

## Giới thiệu dự án

Hệ thống tạo đối thoại gian lận là một khuôn khổ tạo đối thoại đa tác nhân dựa trên mô hình ngôn ngữ lớn, nhằm mục đích tạo ra các tập dữ liệu đối thoại gian lận thực tế cho mục đích nghiên cứu, đào tạo và giáo dục chống gian lận viễn thông. Hệ thống này sử dụng ba tác nhân để làm việc cùng nhau: tác nhân gian lận, tác nhân người dùng và tác nhân quản lý để mô phỏng các loại tình huống gian lận khác nhau và các phản ứng khác nhau của người dùng.

Dữ liệu hội thoại do hệ thống này tạo ra có thể được sử dụng cho:
- Đào tạo các mô hình phát hiện gian lận
- Phát triển các công cụ giáo dục và phòng ngừa
- Nghiên cứu các mô hình và sự tiến hóa của lời nói gian lận
- Phân tích sự khác biệt trong phản ứng với gian lận của các nhóm người dùng khác nhau

## Kiến trúc hệ thống

Hệ thống bao gồm các thành phần cốt lõi sau:

1. **Mô-đun tác nhân**:
- `LeftAgent` (kẻ lừa đảo): chịu trách nhiệm mô phỏng nhiều lời nói và chiến lược gian lận khác nhau
- `RightAgent` (người dùng): mô phỏng phản ứng của người dùng ở nhiều độ tuổi, nghề nghiệp và mức độ nhận thức chống gian lận khác nhau
- `ManagerAgent` (người quản lý): theo dõi cuộc trò chuyện và quyết định khi nào và ai sẽ kết thúc cuộc trò chuyện

2. **Điều phối viên cuộc trò chuyện**:
- Điều phối luồng hội thoại giữa kẻ lừa đảo và người dùng
- Kiểm soát kết thúc cuộc trò chuyện theo quyết định của người quản lý
- Tạo kết thúc cuộc trò chuyện tự nhiên

3. **Công cụ**:
- Đóng gói ứng dụng khách API OpenAI
- Ghi lại cuộc trò chuyện
- Công cụ xuất dữ liệu

## Tính năng

- **Gian lận đa dạng**: Hỗ trợ 15 loại gian lận phổ biến ở Việt Nam:
  1. **Đầu tư**: Lừa đảo đầu tư tài chính, crypto, forex với lời hứa lợi nhuận cao
  2. **Tình cảm**: Lừa đảo tình cảm, kết bạn online rồi xin tiền
  3. **Phishing**: Lừa đảo qua email, SMS, website giả để đánh cắp thông tin
  4. **Chiếm đoạt danh tính**: Thu thập thông tin cá nhân để mạo danh
  5. **Trúng thưởng**: Thông báo giả về việc trúng thưởng để lừa đóng phí
  6. **Việc làm giả**: Quảng cáo việc nhẹ lương cao, yêu cầu đóng phí
  7. **Ngân hàng**: Giả danh ngân hàng để lấy thông tin thẻ, OTP
  8. **Giả danh công an**: Mạo danh công an/viện kiểm sát để đe dọa
  9. **Giả danh tổng đài**: Giả danh nhân viên chăm sóc khách hàng
  10. **Lừa đảo bưu điện**: Giả danh bưu điện báo có bưu phẩm cần đóng phí
  11. **Lừa đảo y tế**: Giả danh bệnh viện/bác sĩ để lừa tiền điều trị
  12. **Lừa đảo học phí**: Giả danh trường học về học bổng/đóng phí
  13. **Lừa đảo thuế**: Giả danh cơ quan thuế về hoàn/phạt thuế
  14. **Lừa đảo từ thiện**: Kêu gọi quyên góp giả
  15. **Lừa đảo mua bán**: Lừa đảo trong giao dịch online
- **Tùy chỉnh chân dung người dùng**: Phản ứng của người dùng có thể được tùy chỉnh dựa trên độ tuổi, nghề nghiệp và mức độ nhận thức chống gian lận
- **Kết thúc cuộc trò chuyện tự nhiên**: Tác nhân quản lý xác định điểm kết thúc tự nhiên và phương thức kết thúc cuộc trò chuyện
- **Tạo song song hiệu quả**: Hỗ trợ tạo song song đa luồng với lượng lớn dữ liệu cuộc trò chuyện
- **Xuất dữ liệu định dạng kép**: Hỗ trợ cả định dạng JSONL hợp lý hóa và định dạng JSON chi tiết
- **Ghi nhật ký chi tiết**: Ghi lại toàn bộ lịch sử cuộc trò chuyện và trạng thái hoạt động của hệ thống
- **Lấy mẫu phân phối đồng đều**: Đảm bảo phân phối đồng đều nhóm tuổi, nhận thức chống gian lận và các loại gian lận

## Yêu cầu cài đặt

### Yêu cầu về môi trường
- Python 3.8 trở lên
- Khóa API hợp lệ (như API OpenAI hoặc API tương thích khác)

### Phụ thuộc
```bash
pip install openai tqdm concurrent.futures
```

## Sử dụng

### Sử dụng cơ bản

1. Cấu hình khóa API và URL cơ sở:
```bash
export OPENAI_API_KEY="your-api-key"
```

2. Chạy tạo hộp thoại đơn:
```bash
python main.py --fraud_type investment --base_url "https://api.siliconflow.cn/v1" --api_key "your-api-key" --model "deepseek-ai/DeepSeek-V2.5"
```

3. Tạo hàng loạt tập dữ liệu hộp thoại:
```bash
python generate_dialogues.py --count 1000 --base_url "https://api.siliconflow.cn/v1" --api_key "your-api-key" --model "deepseek-ai/DeepSeek-V2.5" --workers 10 --output "fraud_dialogues.jsonl" --full_output_dir "full_dialogues"
```

### Mô tả tham số

#### Tạo hộp thoại đơn (main.py)
- `--fraud_type`: Loại gian lận [đầu tư, lãng mạn, lừa đảo, trộm cắp danh tính, xổ số, việc làm, ngân hàng]
- `--user_age`: độ tuổi của người dùng
- `--user_awareness`: nhận thức chống gian lận của người dùng [thấp, trung bình, cao]
- `--max_turns`: số lượt trò chuyện tối đa
- `--output`: đường dẫn tệp đầu ra
- `--base_url`: URL điểm cuối API tùy chỉnh
- `--api_key`: khóa API tùy chỉnh
- `--model`: tên mô hình

#### Tạo hộp thoại hàng loạt (generate_dialogues.py)
- `--count`: tổng số hộp thoại cần tạo
- `--output`: đường dẫn tệp đầu ra định dạng JSONL
- `--full_output_dir`: thư mục đầu ra tệp JSON của hộp thoại đầy đủ
- `--base_url`: URL điểm cuối API tùy chỉnh
- `--api_key`: khóa API tùy chỉnh
- `--model`: tên mô hình
- `--max_turns`: số lượt tối đa cho mỗi hộp thoại
- `--workers`: số luồng được tạo đồng thời

## Định dạng dữ liệu

### Định dạng JSONL (phiên bản đơn giản hóa)
```json
{
    "tts_id": "tts_fraud_00001",
    "left": [
        "Xin chào, đây là Ngân hàng Xây dựng Trung Quốc. Bạn có quỹ dự trữ 300.000 nhân dân tệ đứng tên mình. Lãi suất hàng tháng chỉ thấp tới 2,3%. Bạn có cần tiền ngay không?",
        "Vậy thì hãy cân nhắc nhé. Nếu bạn cần, vui lòng liên hệ với tôi. Đây là thông tin liên hệ của tôi."
    ],
    "right": [
        "Xin chào, không, cảm ơn.",
        "Được rồi, cảm ơn, tạm biệt."
    ],
    "user_age": 22,
    "user_awareness": "medium",
    "fraud_type": "banking",
    "occupation": "student",
    "termination_reason": "Người dùng nói rằng không cần...",
    "terminator": "right"
}
```

### Định dạng JSON (phiên bản chi tiết)
```json
{
    "dialogue_history": [
        {
            "role": "left",
            "content": "Xin chào, đây là Ngân hàng Xây dựng Trung Quốc. Bạn có quỹ dự trữ 300.000 nhân dân tệ đứng tên mình. Lãi suất hàng tháng chỉ thấp tới 2,3%. Bạn có cần tiền ngay không?",
            "timestamp": 1740545473.5704024
        },
        {
            "role": "right",
            "content": "Xin chào, không, cảm ơn bạn.",
            "timestamp": 1740545476.625075
        }
    ],
    "turns": 2,
    "terminated_by_manager": true,
    "termination_reason": "Có. Người dùng đã chấm dứt. Lý do: Người dùng đã từ chối đề xuất của kẻ lừa đảo một cách rõ ràng...",
    "terminator": "right",
    "conclusion_messages": [...],
    "reached_max_turns": false
}
```

## Cấu trúc dự án

```
├── agents/ # Mô-đun tác nhân
│ ├── base_agent.py # Lớp trừu tượng tác nhân cơ sở
│ ├── left_agent.py # Tác nhân lừa đảo
│ ├── right_agent.py # Tác nhân người dùng
│ ├── manager_agent.py # Tác nhân quản lý
│ └── prompts/ # Mẫu lời nhắc
│ ├── left_prompts.py
│ ├── right_prompts.py
│ └── manager_prompts.py
├── logic/ # Logic nghiệp vụ
│ └── dialogue_orchestrator.py # Điều phối viên đối thoại
├── utils/ # Lớp tiện ích
│ ├── openai_client.py # Máy khách API OpenAI
│ └── conversation_logger.py # Trình ghi nhật ký đối thoại
├── config.py # Tệp cấu hình
├── main.py # Mục tạo đối thoại đơn lẻ
├── generate_dialogues.py # Tạo đối thoại hàng loạt entry
├── requirements.txt # Danh sách gói phụ thuộc
└── README.md # Mô tả dự án
```

## Mô tả chi tiết các loại lừa đảo

1. **Lừa đảo đầu tư (Đầu tư)**: Dụ dỗ người dùng đầu tư vào crypto, forex, chứng khoán với lời hứa lợi nhuận cao, ít rủi ro
2. **Lừa đảo tình cảm (Tình cảm)**: Thiết lập mối quan hệ tình cảm giả trên mạng, sau đó xin tiền với nhiều lý do khác nhau
3. **Lừa đảo phishing (Phishing)**: Giả danh website/dịch vụ chính thống để đánh cắp thông tin đăng nhập, mật khẩu
4. **Chiếm đoạt danh tính (Chiếm đoạt danh tính)**: Thu thập thông tin cá nhân (CMND, CCCD, số thẻ) để mạo danh thực hiện tội phạm
5. **Lừa đảo trúng thưởng (Trúng thưởng)**: Thông báo giả về việc trúng giải lớn, yêu cầu đóng phí thuế/xử lý để nhận thưởng
6. **Lừa đảo việc làm (Việc làm giả)**: Quảng cáo việc nhẹ lương cao, làm online, yêu cầu đóng phí đào tạo/bảo hiểm
7. **Lừa đảo ngân hàng (Ngân hàng)**: Giả danh nhân viên ngân hàng để lấy thông tin thẻ, mã PIN, OTP
8. **Giả danh công an (Giả danh công an)**: Mạo danh công an/viện kiểm sát/tòa án, đe dọa bắt giữ, yêu cầu chuyển tiền bảo lãnh
9. **Giả danh tổng đài (Giả danh tổng đài)**: Giả danh nhân viên chăm sóc khách hàng ngân hàng/viễn thông để lấy thông tin
10. **Lừa đảo bưu điện (Lừa đảo bưu điện)**: Giả danh nhân viên bưu điện báo có bưu phẩm/tiền chuyển phát cần đóng phí xử lý
11. **Lừa đảo y tế (Lừa đảo y tế)**: Giả danh bệnh viện/bác sĩ báo kết quả xét nghiệm bất thường, cần điều trị gấp
12. **Lừa đảo học phí (Lừa đảo học phí)**: Giả danh trường học thông báo học bổng hoặc yêu cầu đóng học phí/lệ phí gấp
13. **Lừa đảo thuế (Lừa đảo thuế)**: Giả danh cơ quan thuế thông báo hoàn thuế hoặc phạt thuế, yêu cầu thông tin tài khoản
14. **Lừa đảo từ thiện (Lừa đảo từ thiện)**: Kêu gọi quyên góp giả cho hoàn cảnh khó khăn, thiên tai, tạo cảm xúc thương hại
15. **Lừa đảo mua bán (Lừa đảo mua bán)**: Lừa đảo trong giao dịch mua bán online, ship COD giả, yêu cầu chuyển tiền trước
8. **Giả danh công an (police_scam)**: Mạo danh cảnh sát thông báo nạn nhân liên quan đến vụ án, đe dọa bắt giữ nếu không chuyển tiền
9. **Lừa đảo bưu điện (postal_scam)**: Giả danh nhân viên bưu điện báo có bưu phẩm chứa tiền/tài sản nhưng cần đóng phí
10. **Lừa đảo y tế (medical_scam)**: Giả danh bệnh viện/bác sĩ báo kết quả xét nghiệm có vấn đề, cần điều trị gấp
11. **Lừa đảo học phí (tuition_scam)**: Giả danh trường học thông báo được học bổng hoặc cần đóng học phí gấp
12. **Lừa đảo thuế (tax_scam)**: Giả danh cơ quan thuế báo có tiền hoàn thuế hoặc bị phạt thuế, cần cung cấp thông tin tài khoản
13. **Lừa đảo từ thiện (charity_scam)**: Kêu gọi quyên góp cho hoàn cảnh khó khăn/thiên tai giả
14. **Lừa đảo mua bán online (online_sales_scam)**: Giả danh người mua/bán hàng online, yêu cầu chuyển tiền trước hoặc ship COD với giá trị cao hơn

## Tham số người dùng chi tiết

### 1. **Độ tuổi (user_age)**:
- **18-25**: Thanh niên (sinh viên, nhân viên mới vào nghề)
- **26-40**: Người trưởng thành (nhân viên văn phòng, khởi nghiệp)
- **41-55**: Trung niên (quản lý, kinh doanh)
- **56-70**: Cao tuổi (chuẩn bị/đã nghỉ hưu)

### 2. **Mức độ nhận thức về lừa đảo (user_awareness)**:
- **thấp**: Ít hiểu biết về lừa đảo, dễ tin tưởng, thường là người cao tuổi hoặc ít tiếp xúc công nghệ
- **trung bình**: Có kiến thức cơ bản nhưng vẫn có thể bị lừa bởi những chiêu trò tinh vi
- **cao**: Hiểu rõ về lừa đảo, cảnh giác cao, thường là người trẻ hoặc có hiểu biết về công nghệ

### 3. **Nghề nghiệp (occupation)**:
- **sinh viên**: Đối tượng hay bị nhắm vào với lừa đảo học phí, việc làm part-time
- **nhân viên văn phòng**: Quan tâm đến đầu tư, thăng tiến, thường bận rộn
- **người nghỉ hưu**: Ít hiểu công nghệ, có thời gian, quan tâm sức khỏe
- **nội trợ**: Quan tâm gia đình, tiết kiệm, việc làm tại nhà  
- **kinh doanh**: Hiểu tài chính, quan tâm cơ hội đầu tư
- **giáo viên**: Có hiểu biết, thận trọng, quan tâm giáo dục
- **công nhân**: Thu nhập hạn chế, quan tâm việc làm thêm
- **nông dân**: Ít hiểu công nghệ, thẳng thắn, quan tâm chính sách nông nghiệp
- **tự do**: Hiểu công nghệ, cảnh giác với cơ hội làm việc mới
- **khác**: Các nghề nghiệp khác

## Người đóng góp

Dự án này được phát triển bởi [tên nhóm hoặc tổ chức của bạn].

## Tuyên bố miễn trừ trách nhiệm

Dự án này chỉ dành cho mục đích nghiên cứu, giáo dục và phòng ngừa gian lận viễn thông. Nghiêm cấm sử dụng nội dung do hệ thống này tạo ra cho bất kỳ mục đích bất hợp pháp hoặc phi đạo đức nào. Người dùng phải chịu hoàn toàn trách nhiệm về việc sử dụng hệ thống này và nội dung do hệ thống tạo ra.

## Giấy phép

[Giấy phép phù hợp, chẳng hạn như MIT, Apache, v.v.]

---

## Mapping loại lừa đảo

Hệ thống hỗ trợ cả tên tiếng Việt và tiếng Anh cho các loại lừa đảo:

Chắc chắn rồi, đây là bảng được định dạng lại bằng các ký tự `|` và `--` để tạo thành một bảng văn bản thuần túy.

```
| Tiếng Việt                | Tiếng Anh                   | Mô tả                           |
|---------------------------|-----------------------------|---------------------------------|
| Đầu tư                    | investment                  | Lừa đảo đầu tư tài chính        |
| Tình cảm                  | romance                     | Lừa đảo tình cảm online         |
| Phishing                  | phishing                    | Lừa đảo qua website/email giả   |
| Chiếm đoạt danh tính      | identity_theft              | Thu thập thông tin cá nhân      |
| Trúng thưởng              | lottery                     | Thông báo trúng giải giả        |
| Việc làm giả              | fake_job                    | Quảng cáo việc làm giả          |
| Ngân hàng                 | banking                     | Giả danh ngân hàng              |
| Giả danh công an          | impersonation_police        | Mạo danh cơ quan công an        |
| Giả danh tổng đài         | impersonation_call_center   | Giả danh dịch vụ khách hàng     |
| Lừa đảo bưu điện          | postal_scam                 | Giả danh bưu điện               |
| Lừa đảo y tế              | medical_scam                | Giả danh cơ sở y tế             |
| Lừa đảo học phí           | education_scam              | Giả danh cơ sở giáo dục         |
| Lừa đảo thuế              | tax_scam                    | Giả danh cơ quan thuế           |
| Lừa đảo từ thiện          | charity_scam                | Kêu gọi từ thiện giả            |
| Lừa đảo mua bán           | ecommerce_scam              | Lừa đảo thương mại điện tử      |
```


## Câu hỏi thường gặp

### Q: Làm thế nào để chọn loại lừa đảo phù hợp cho nghiên cứu?
**A**: Chọn dựa trên:
- **Mục tiêu nghiên cứu**: Muốn nghiên cứu loại nào cụ thể
- **Đối tượng mục tiêu**: Người cao tuổi → y tế, thuế; Sinh viên → học phí, việc làm
- **Tính thời sự**: Các loại đang phổ biến hiện tại

### Q: Tham số nào ảnh hưởng nhiều nhất đến kết quả hội thoại?
**A**: Theo thứ tự ưu tiên:
1. **Mức độ nhận thức** (awareness): Quyết định nạn nhân có bị lừa hay không
2. **Nghề nghiệp** (occupation): Ảnh hưởng đến chủ đề quan tâm và phản ứng
3. **Độ tuổi** (age): Ảnh hưởng đến ngôn ngữ và cách tiếp cận

### Q: Làm sao để tạo hội thoại cân bằng giữa các loại?
**A**: Sử dụng tham số `--count` chia hết cho 15 (số loại lừa đảo) để đảm bảo phân bổ đều. Ví dụ: `--count 150` sẽ tạo 10 hội thoại cho mỗi loại.

### Q: Có thể tùy chỉnh kịch bản cho từng vùng miền Việt Nam không?
**A**: Có thể chỉnh sửa prompt trong thư mục `agents/prompts/` để thêm đặc trưng ngôn ngữ, văn hóa từng vùng.

### Q: Làm thế nào để đánh giá chất lượng hội thoại sinh ra?
**A**: Kiểm tra:
- **Tính tự nhiên**: Hội thoại có mạch lạc, logic không
- **Tính sát thực**: Có giống với kịch bản lừa đảo thực tế không  
- **Tính đa dạng**: Các phản ứng có đa dạng theo tham số không
- **Tính kết thúc**: Hội thoại có kết thúc hợp lý không

### Q: Có thể sử dụng với model khác ngoài DeepSeek không?
**A**: Có, chỉ cần model tương thích với OpenAI API format. Đã test với:
- GPT-3.5/GPT-4 (OpenAI)
- Claude (Anthropic - qua proxy)
- Các model local qua Ollama
- Các model trên SiliconFlow, Together AI

### Q: Làm thế nào để tôi thêm một loại gian lận mới?

Trả lời: Thêm loại mới vào danh sách `FRAUD_TYPES` trong `config.py`, sau đó thêm mẫu từ nhắc tương ứng vào `agents/prompts/left_prompts.py`.

### Q: Làm thế nào để tôi điều chỉnh điều kiện kết thúc của cuộc trò chuyện?

Trả lời: Sửa đổi phần điều kiện kết thúc của `MANAGER_SYSTEM_PROMPT` trong `agents/prompts/manager_prompts.py`.

### Q: Làm thế nào để tôi cải thiện hiệu quả tạo?

Trả lời: Tăng giá trị tham số `--workers` có thể cải thiện khả năng xử lý song song, nhưng bạn cần chú ý đến giới hạn lệnh gọi API và mức tiêu thụ tài nguyên hệ thống.

### H: Làm thế nào để tùy chỉnh chân dung người dùng?
A: Thêm hồ sơ người dùng được cài đặt sẵn thông qua các tham số `--user_age`, `--user_awareness` hoặc trong từ điển `USER_PROFILES` trong `config.py`.

## Ví dụ sử dụng các loại lừa đảo mới

### 1. Lừa đảo giả danh công an
```bash
python generate_dialogues.py \
  --count 10 \
  --output "dialogues_police_scam.jsonl" \
  --base_url "https://api.siliconflow.cn/v1" \
  --api_key "your-api-key" \
  --model "deepseek-ai/DeepSeek-V2.5"
```

**Kịch bản mẫu**: Kẻ lừa đảo giả danh cảnh sát báo nạn nhân liên quan đến vụ án, đe dọa bắt giữ, yêu cầu chuyển tiền để "chứng minh trong sạch".

### 2. Lừa đảo bưu điện
```bash
python main.py \
  --fraud_type "Lừa đảo bưu điện" \
  --age 50 \
  --awareness "thấp" \
  --occupation "nông dân"
```

**Kịch bản mẫu**: Giả danh nhân viên bưu điện báo có bưu phẩm chứa tiền/tài sản nhưng cần đóng phí thuế/xử lý.

### 3. Lừa đảo y tế
```bash
python main.py \
  --fraud_type "Lừa đảo y tế" \
  --age 65 \
  --awareness "thấp" \
  --occupation "người nghỉ hưu"
```

**Kịch bản mẫu**: Giả danh bệnh viện/bác sĩ báo kết quả xét nghiệm có vấn đề, cần điều trị gấp hoặc có tiền bảo hiểm hoàn lại.

### 4. Lừa đảo học phí
```bash
python main.py \
  --fraud_type "Lừa đảo học phí" \
  --age 20 \
  --awareness "trung bình" \
  --occupation "sinh viên"
```

**Kịch bản mẫu**: Giả danh trường học thông báo được học bổng hoặc cần đóng học phí gấp để giữ chỗ.

### 5. Lừa đảo thuế
```bash
python main.py \
  --fraud_type "Lừa đảo thuế" \
  --age 40 \
  --awareness "trung bình" \
  --occupation "kinh doanh"
```

**Kịch bản mẫu**: Giả danh cơ quan thuế báo có tiền hoàn thuế hoặc bị phạt thuế, cần cung cấp thông tin tài khoản.

### 6. Lừa đảo từ thiện
```bash
python main.py \
  --fraud_type "Lừa đảo từ thiện" \
  --age 45 \
  --awareness "trung bình" \
  --occupation "nội trợ"
```

**Kịch bản mẫu**: Kêu gọi quyên góp cho hoàn cảnh khó khăn/thiên tai giả, tạo cảm xúc thương hại.

### 7. Lừa đảo mua bán online
```bash
python main.py \
  --fraud_type "Lừa đảo mua bán" \
  --age 30 \
  --awareness "cao" \
  --occupation "nhân viên văn phòng"
```

**Kịch bản mẫu**: Giả danh người mua/bán hàng online, yêu cầu chuyển tiền trước hoặc ship COD với giá trị cao hơn.

### Ví dụ sinh hội thoại hàng loạt với tất cả loại lừa đảo mới
```bash
python generate_dialogues.py \
  --count 150 \
  --output "all_fraud_types_dialogues.jsonl" \
  --full_output_dir "detailed_dialogues" \
  --base_url "https://api.siliconflow.cn/v1" \
  --api_key "your-api-key" \
  --model "deepseek-ai/DeepSeek-V2.5" \
  --max_turns 20 \
  --workers 5
```

**Kết quả**: Sinh 150 hội thoại bao phủ tất cả 15 loại lừa đảo, phân bổ đều các độ tuổi, mức độ nhận thức và nghề nghiệp.