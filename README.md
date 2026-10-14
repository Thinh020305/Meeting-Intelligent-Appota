<<<<<<< HEAD
# Meeting-Intelligent-Appota
MVP hệ thống phân tích cuộc họp
=======
# Meeting Intelligence MVP

Phân tích transcript qua preprocessing → extraction → relationship resolution → final state resolution. `POST /analyze` trả đúng 8 nhóm theo Final Output Contract; UI hiển thị kết quả và nội dung evidence gốc.

## Cài đặt và chạy

Deploy lên Render: xem [DEPLOY_RENDER.md](DEPLOY_RENDER.md). UI đọc `API_BASE_URL` từ environment của service để trỏ tới backend đã deploy.

Thiết kế cho Python 3.11, Pydantic v2. Chạy các lệnh PowerShell trong thư mục project:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Điền `GEMINI_API_KEY` và `LLM_MODEL` trong `.env` (đã có sẵn mẫu rỗng), hoặc đặt hai biến môi trường. Model phải là tên Gemini hỗ trợ structured output và khả dụng trên Free Tier của tài khoản; ứng dụng không có model mặc định. Biến môi trường được ưu tiên hơn `.env`. API key chỉ được dùng ở backend.

Mở hai terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Mở [UI](http://127.0.0.1:8501) hoặc [API docs](http://127.0.0.1:8000/docs). Paste transcript và bấm Analyze. Ví dụ gọi API:

```powershell
$body = @{ transcript = "PM: Nam hoàn thành API trước thứ Sáu nhé." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/analyze -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

## Transcript và evidence

Mỗi dòng không rỗng tạo một segment, theo đúng thứ tự input. Hỗ trợ `Nam: nội dung`, `[00:01:20] Nam: nội dung`, `Nam: [00:01:20] nội dung`, text không có metadata, và nhãn `seg_001` có sẵn. Nhãn ở một dòng riêng được gắn vào dòng phát biểu kế tiếp. Dấu `→` chỉ tách segment khi theo sau là nhãn `seg_NNN`, như bảng testcase của specification. ID tự tạo tránh trùng với nhãn đã cung cấp. Không sắp xếp lại theo timestamp, không đoán speaker/timestamp, không sửa nội dung phát biểu.

API chỉ trả 8 nhóm, không thêm transcript/debug metadata vào output. UI dùng cùng hàm preprocessing để tra evidence IDs sang các đoạn gốc đã nhập. Owner/deadline/requester/target thiếu là JSON `null`.

## Contracts và LLM

- `app/schemas/meeting_output.py`: contracts Pydantic v2, cấm field thừa, bắt buộc tất cả field chính thức, kiểm tra evidence và event references theo input của từng bước.
- `app/services/llm_client.py`: nơi duy nhất gọi Gemini, đọc prompt `.txt`, gửi JSON schema, validate response, xử lý timeout/quota/response không hợp lệ. Không trả raw provider errors hoặc credentials cho người dùng.
- Ba service nhận/trả model trong memory. Relationship output dùng `threads`; input final dùng `event_threads` theo contract tương ứng. `reason` luôn bắt buộc dù một số ví dụ trong tài liệu bỏ field này.
- Ba prompt chứa phần tương ứng từ specification, bổ sung yêu cầu ưu tiên contract. Final output không có `status`; task đã completed, problem resolved, obstacle cleared không nằm trong nhóm active. Task bị blocked vẫn được giữ cùng obstacle.
- Provider nằm sau interface `LLMClient`; thay provider bằng implementation mới tại gateway và dependency `get_llm_client`, không sửa logic các bước.
- Mỗi phân tích chạy đủ 3 LLM calls kể cả khi extraction rỗng. Chỉ retry lỗi quota hoặc HTTP tạm thời, tối đa 2 lần mỗi bước. Không tự sửa JSON, bỏ record lỗi hoặc trả kết quả giả khi Gemini thất bại.

Không dùng database, vector database, LangChain, LangGraph, fine-tuning, hoặc ghi dữ liệu runtime giữa các bước ra file. `.env` chỉ lưu cấu hình; tests dùng các fixture tĩnh. UI giữ kết quả hiện tại trong session memory.

Transport/schema theo [Gemini GenerateContent API](https://ai.google.dev/api/generate-content) và [structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output). Structured output bảo đảm cấu trúc, không bảo đảm mọi kết luận ngữ nghĩa; độ chính xác thực tế cần kiểm tra bằng bộ live tests dưới đây.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

10 testcase gốc nằm trong `tests/sample_transcripts/01.txt` đến `10.txt`. `cases.py` chứa golden responses cho cả 3 bước. Các tests thông thường đi qua endpoint và `llm_client.py` thật với HTTP Gemini giả lập, kiểm tra truyền đầy đủ dữ liệu, prompt từ file, JSON schema, output và lỗi validation; thêm tests preprocessing, provider failures/retry và Streamlit UI.

Mock tests kiểm tra tích hợp và contracts, không chứng minh Gemini hiểu đúng cả 10 transcript. Bộ live tests kiểm tra Gemini thật theo category/state/owner/deadline và các quan hệ ACCEPTS, BLOCKS, RESOLVES; không đòi câu chữ summary giống hệt fixture:

```powershell
$env:RUN_LIVE_GEMINI = '1'
.\.venv\Scripts\python.exe -m pytest -q -m live
```

Bộ live chạy 10 phân tích, tối thiểu 30 Gemini calls; quota của tài khoản có thể giới hạn một lần chạy. Không bật `RUN_LIVE_GEMINI` thì 10 live tests được skip. HTTP 422 là input không hợp lệ; 503 là thiếu cấu hình; 502 là lỗi Gemini hoặc output không đúng contract. Kết quả lỗi không có partial output.

Kiểm tra trong workspace hiện tại: 67 tests passed, 10 live tests skipped; API OpenAPI và Streamlit health endpoint hoạt động. Máy hiện có Python 3.13 nên lần chạy này dùng Python 3.13; source dùng cú pháp tương thích Python 3.11, nhưng chưa được chạy kiểm chứng trên interpreter 3.11. Chưa đánh giá Gemini thật vì cấu hình API key/model đang rỗng.
>>>>>>> de277be (initial commit)
