# Deploy lên Render

Dùng 2 Web Services từ cùng một repository: FastAPI và Streamlit. Không cần database. Lệnh bên dưới chạy trên Linux của Render, không dùng `.venv` từ Windows.

## 1. Upload code lên GitHub

Tạo repository chỉ chứa nội dung thư mục `Meeting Intelligent`. Repo root phải có `app/`, `ui/`, `requirements.txt`, `.python-version` và `.gitignore`.

Không upload `.env`, `.venv`, `__pycache__` hoặc `.pytest_cache`. File `.env.example` chỉ được chứa giá trị mẫu, không chứa API key thật. Repository có thể để private và cấp Render quyền truy cập.

Workspace hiện nằm dưới một Git repository ở thư mục cha. Nếu dùng Git CLI, tạo repository riêng trong `Meeting Intelligent` trước khi add/commit; không add toàn bộ Desktop. Nếu upload qua giao diện GitHub, chọn đúng các file project và bật hiển thị file ẩn để upload `.python-version` và `.gitignore`.

## 2. Tạo FastAPI backend

Render Dashboard → New → Web Service → chọn repo và branch chứa code.

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Root Directory | Để trống nếu code ở repo root |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free để thử MVP |
| Health Check Path | `/openapi.json` |

Trong Environment của backend, đặt `GEMINI_API_KEY` bằng key đang dùng local và `LLM_MODEL` bằng tên model hiện tại. Không upload `.env` để truyền key. File `.python-version` chọn Python 3.11; không cần đặt `PYTHON_VERSION`.

Deploy và đợi trạng thái Live. Sao chép URL public HTTPS Render cấp; mở `<URL API>/docs`, thử `POST /analyze` với transcript ngắn. Health check không gọi Gemini.

## 3. Tạo Streamlit UI

New → Web Service → chọn cùng repo và branch.

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Root Directory | Để trống nếu code ở repo root |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m streamlit run ui/streamlit_app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true --browser.gatherUsageStats false` |
| Instance Type | Free để thử MVP |
| Health Check Path | `/_stcore/health` |

Trong Environment của UI, đặt `API_BASE_URL` bằng nguyên URL public HTTPS của backend ở bước 2, không thêm `/analyze` hoặc `/docs`. Dùng đúng URL Render cấp, không tự đoán hostname. Free services không nhận private network traffic nên dùng URL public.

UI không cần API key. Streamlit server gửi request đến FastAPI, trình duyệt không trực tiếp gọi FastAPI nên kiến trúc hiện tại không cần thêm CORS.

Deploy UI, mở URL UI, kiểm tra ô Địa chỉ API rồi nhập:

```text
PM: Nam hoàn thành API trước thứ Sáu nhé.
```

Bấm Analyze. Kết quả phải đủ 8 nhóm, task có owner Nam, deadline thứ Sáu và evidence.

## 4. Vận hành MVP

- Đổi API key/model: cập nhật Environment và deploy/restart backend.
- Đổi URL backend: cập nhật `API_BASE_URL` và deploy/restart UI.
- HTTP 503: thiếu cấu hình; HTTP 502: lỗi Gemini, quota, kết nối hoặc output không đúng contract. Xem Logs của service tương ứng.
- Free services ngủ sau 15 phút không có inbound traffic, lần truy cập tiếp theo có thể mất khoảng một phút để thức dậy. Nếu Analyze lỗi lúc backend đang thức dậy, đợi backend Live rồi thử lại.
- 750 giờ Free instance mỗi tháng được chia sẻ giữa các Free services trong workspace.

Tài liệu: [FastAPI](https://render.com/docs/deploy-fastapi), [Port binding](https://render.com/docs/web-services), [Python version](https://render.com/docs/python-version), [Free Tier](https://render.com/docs/free).
