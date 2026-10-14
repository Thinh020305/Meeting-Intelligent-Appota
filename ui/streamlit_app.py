import json
import os
import sys
from pathlib import Path

import httpx
import streamlit as st
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.schemas.meeting_output import MeetingOutput
from app.services.preprocessing import preprocess

st.set_page_config(page_title="Meeting Intelligence", page_icon="📝", layout="wide")
st.title("Meeting Intelligence")
st.write("Nhập transcript để xem thông tin còn hiệu lực khi cuộc họp kết thúc, kèm bằng chứng.")
with st.sidebar:
    api_url = st.text_input("Địa chỉ API", os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    st.caption("Mỗi dòng là một segment. Có thể dùng Nam: nội dung hoặc [00:01:20] Nam: nội dung.")
with st.form("analyze_form"):
    transcript = st.text_area("Transcript cuộc họp", height=280)
    submitted = st.form_submit_button("Analyze", type="primary")

if submitted:
    st.session_state.pop("analysis", None)
    try:
        segments = preprocess(transcript)
        with st.spinner("Đang trích xuất, phân giải quan hệ và xác định trạng thái cuối..."):
            response = httpx.post(f"{api_url.rstrip('/')}/analyze", json={"transcript": transcript}, timeout=330)
            if response.is_error:
                try:
                    detail = response.json().get("detail", "Không thể phân tích transcript")
                except ValueError:
                    detail = "API trả về phản hồi không hợp lệ"
                st.error(f"HTTP {response.status_code}: {detail}")
            else:
                output = MeetingOutput.model_validate(response.json(), context={
                    "segment_ids": {s.segment_id for s in segments},
                })
                st.session_state.analysis = (output.model_dump(), [s.model_dump() for s in segments])
    except (ValueError, ValidationError):
        st.error("Transcript hoặc kết quả không đúng contract. Kiểm tra nội dung và segment IDs.")
    except httpx.TimeoutException:
        st.error("Phân tích quá thời gian chờ. Hãy thử lại.")
    except httpx.RequestError:
        st.error("Không kết nối được API. Hãy khởi động FastAPI và kiểm tra địa chỉ.")

if "analysis" in st.session_state:
    output, source = st.session_state.analysis
    source_by_id = {s["segment_id"]: s for s in source}
    labels = {
        "decisions": "Quyết định", "tasks": "Công việc", "problems": "Vấn đề",
        "requests": "Yêu cầu", "obstacles": "Vướng mắc", "feedback": "Phản hồi",
        "unfinalized_content": "Nội dung chưa chốt", "risks": "Rủi ro",
    }
    for group, label in labels.items():
        with st.expander(f"{label} ({len(output[group])})", expanded=bool(output[group])):
            if not output[group]:
                st.caption("Không có thông tin trong nhóm này.")
            for record in output[group]:
                st.write(record["content"])
                for field in ("owner", "deadline", "requester", "target"):
                    if field in record:
                        st.caption(f"{field}: {record[field] if record[field] is not None else 'null'}")
                for segment_id in record["evidence_segment_ids"]:
                    segment = source_by_id[segment_id]
                    metadata = " · ".join(str(segment[k]) for k in ("speaker", "timestamp") if segment[k])
                    st.text(f"{segment_id}{' · ' + metadata if metadata else ''}: {segment['text']}")
    with st.expander("JSON"):
        st.json(output)
    st.download_button("Tải JSON", json.dumps(output, ensure_ascii=False, indent=2),
                       file_name="meeting_output.json", mime="application/json")
