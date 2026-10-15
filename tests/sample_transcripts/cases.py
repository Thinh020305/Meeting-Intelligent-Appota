"""Seven mocked golden cases matching the edited transcript files 01–07.

These fixtures are expectations, not an extraction engine or production fallback.
"""

from pathlib import Path

GROUPS = ("decisions", "tasks", "problems", "requests", "obstacles", "feedback", "unfinalized_content", "risks")


def record(content, *segments, **fields):
    return {"content": content, **fields,
            "evidence_segment_ids": [f"seg_{s:03}" for s in segments]}


def event(kind, content, subject, segment, actor, **fields):
    return {"event_type": kind, "subject": subject, "actor": actor,
            "target": None, "owner": None, "deadline": None,
            **record(content, segment), **fields}


def task(content, segment, owner=None, deadline=None):
    return record(content, segment, owner=owner, deadline=deadline)


def request(content, segment, requester, target=None):
    return record(content, segment, requester=requester, target=target)


def case(number, events, final, relations=()):
    events = [{"event_id": f"evt_{i:03}", "order": i, **e} for i, e in enumerate(events, 1)]
    topics = {}
    for e in events:
        topics.setdefault(e["subject"], []).append(e["event_id"])
    threads = [{"thread_id": f"thread_{i:03}", "topic": topic, "event_ids": ids}
               for i, (topic, ids) in enumerate(topics.items(), 1)]
    relationships = [{"from_event": f"evt_{a:03}", "to_event": f"evt_{b:03}",
                      "relation": rel, "reason": reason} for a, b, rel, reason in relations]
    return {"id": f"{number:02}",
            "transcript": Path(__file__).with_name(f"{number:02}.txt").read_text(encoding="utf-8"),
            "extraction": {"candidate_events": events},
            "relationship": {"threads": threads, "relationships": relationships},
            "final": {group: final.get(group, []) for group in GROUPS}}


CASES = [
    # MVP scope, explicit assignments, and an active testing blocker.
    case(1, [
        event("DECISION_PROPOSAL", "Sử dụng PostgreSQL cho MVP", "database", 2, "Bình"),
        event("DECISION_ACCEPTANCE", "Sử dụng PostgreSQL cho MVP", "database", 3, "An"),
        event("TASK_CREATED", "Thiết kế database schema", "database_schema", 4, "Chi", owner="Chi", deadline="trước ngày 20/10/2026"),
        event("TASK_CREATED", "Triển khai API đăng nhập", "login_api", 5, "An", target="Bình", owner="Bình", deadline="trước ngày 22/10/2026"),
        event("PROBLEM_RAISED", "API đăng nhập chưa có môi trường kiểm thử", "test_environment", 7, "Chi"),
        event("OBSTACLE_RAISED", "Thiếu môi trường kiểm thử đang chặn kiểm thử tích hợp", "test_environment", 8, "Bình"),
        event("TASK_CREATED", "Cấu hình môi trường kiểm thử", "test_environment", 9, "An", owner="An", deadline="trước ngày 17/10/2026"),
        event("REQUEST", "Hỗ trợ lọc danh sách công việc theo trạng thái", "task_filter", 10, "Chi"),
        event("DECISION_ACCEPTANCE", "Bổ sung lọc công việc theo trạng thái vào MVP", "task_filter", 11, "An"),
        event("FEEDBACK", "Giao diện dễ sử dụng nhưng điều hướng giữa các trang chưa trực quan", "ui", 12, "Bình"),
    ], {
        "decisions": [record("Sử dụng PostgreSQL cho MVP", 3), record("Bổ sung lọc công việc theo trạng thái vào MVP", 10, 11)],
        "tasks": [task("Thiết kế database schema", 4, "Chi", "trước ngày 20/10/2026"),
                  task("Triển khai API đăng nhập", 5, "Bình", "trước ngày 22/10/2026"),
                  task("Cấu hình môi trường kiểm thử", 9, "An", "trước ngày 17/10/2026")],
        "problems": [record("API đăng nhập chưa có môi trường kiểm thử", 7)],
        "obstacles": [record("Thiếu môi trường kiểm thử đang chặn kiểm thử tích hợp", 8)],
        "requests": [request("Hỗ trợ lọc danh sách công việc theo trạng thái", 10, "Chi")],
        "feedback": [record("Giao diện dễ sử dụng nhưng điều hướng giữa các trang chưa trực quan", 12)],
    }, [
        (2, 1, "ACCEPTS", "An chốt PostgreSQL sau đề xuất của Bình."),
        (9, 8, "ACCEPTS", "An đồng ý bổ sung yêu cầu lọc vào MVP."),
    ]),
    # PostgreSQL explicitly replaces the earlier MongoDB decision.
    case(2, [
        event("DECISION_PROPOSAL", "Lưu kết quả phân tích vào MongoDB", "analysis_database", 1, "An"),
        event("FEEDBACK", "MongoDB linh hoạt với dữ liệu JSON", "analysis_database", 2, "Bình"),
        event("DECISION_ACCEPTANCE", "Tạm chốt MongoDB", "analysis_database", 3, "An"),
        event("DECISION_PROPOSAL", "Dùng PostgreSQL để truy vấn quan hệ giữa các bản ghi", "analysis_database", 4, "Chi"),
        event("DECISION_PROPOSAL", "Chuyển sang PostgreSQL", "analysis_database", 5, "Bình"),
        event("DECISION_REJECTION", "Quyết định MongoDB không còn hiệu lực", "analysis_database", 6, "An"),
        event("DECISION_ACCEPTANCE", "Sử dụng PostgreSQL", "analysis_database", 6, "An"),
        event("TASK_CREATED", "Thiết kế schema PostgreSQL", "postgresql_schema", 7, "Chi", owner="Chi", deadline="trước ngày 21/10/2026"),
        event("UNFINALIZED_CANDIDATE", "Chưa chọn database hay object storage để lưu transcript gốc", "transcript_storage", 8, "Bình"),
        event("UNFINALIZED_CANDIDATE", "Để việc lưu transcript gốc sang cuộc họp tuần sau", "transcript_storage", 9, "An"),
    ], {
        "decisions": [record("Sử dụng PostgreSQL thay cho MongoDB để lưu kết quả phân tích", 6)],
        "tasks": [task("Thiết kế schema PostgreSQL", 7, "Chi", "trước ngày 21/10/2026")],
        "feedback": [record("MongoDB linh hoạt với dữ liệu JSON", 2)],
        "unfinalized_content": [record("Chưa chọn database hay object storage để lưu transcript gốc; xem xét ở cuộc họp tuần sau", 8, 9)],
    }, [
        (3, 1, "ACCEPTS", "An tạm chốt đề xuất MongoDB."),
        (6, 3, "REJECTS", "An tuyên bố quyết định MongoDB không còn hiệu lực."),
        (7, 5, "ACCEPTS", "An chốt chuyển sang PostgreSQL."),
        (7, 3, "SUPERSEDES", "PostgreSQL thay thế quyết định MongoDB trước đó."),
    ]),
    # Keep the PDF request without inventing an owner, deadline, or task.
    case(3, [
        event("REQUEST", "Xuất kết quả phân tích cuộc họp thành PDF", "pdf_export", 1, "An"),
        event("FEEDBACK", "Tính năng xuất PDF nên làm sớm", "pdf_export", 2, "Bình"),
        event("UNFINALIZED_CANDIDATE", "Chưa xác định người thực hiện xuất PDF", "pdf_export", 4, "An"),
        event("UNFINALIZED_CANDIDATE", "Ghi nhận yêu cầu PDF; người thực hiện và thời hạn quyết định sau", "pdf_export", 7, "An"),
        event("UNFINALIZED_CANDIDATE", "Chưa quyết định xuất Word, cần kiểm tra nhu cầu", "word_export", 9, "An"),
    ], {
        "requests": [request("Xuất kết quả phân tích cuộc họp thành PDF", 1, "An")],
        "feedback": [record("Tính năng xuất PDF nên làm sớm", 2)],
        "unfinalized_content": [record("Chưa xác định người thực hiện và thời hạn cho yêu cầu xuất PDF", 7),
                                record("Chưa quyết định xuất Word, cần kiểm tra nhu cầu", 8, 9)],
    }, [(4, 1, "REFERS_TO", "An giữ yêu cầu PDF nhưng để ngỏ người thực hiện và thời hạn.")]),
    # Separate current failure, testing blocker, and future risks.
    case(4, [
        event("PROBLEM_RAISED", "API phân tích transcript bị timeout với dữ liệu dài", "transcript_timeout", 1, "An"),
        event("PROBLEM_RAISED", "Transcript khoảng 30.000 từ xử lý vượt timeout server", "transcript_timeout", 2, "Bình"),
        event("OBSTACLE_RAISED", "Lỗi timeout chặn kiểm thử các cuộc họp dài", "transcript_timeout", 3, "Chi"),
        event("RISK_RAISED", "Hệ thống có thể timeout khi khách hàng thử transcript dài trong demo", "demo_timeout", 4, "An"),
        event("TASK_CREATED", "Kiểm tra lại timeout configuration", "transcript_timeout", 5, "Bình", owner="Bình", deadline="trước ngày 17/10/2026"),
        event("DECISION_PROPOSAL", "Bổ sung xử lý bất đồng bộ", "async_processing", 6, "Chi"),
        event("UNFINALIZED_CANDIDATE", "Chưa chốt xử lý bất đồng bộ, cần đánh giá tác động", "async_processing", 7, "An"),
        event("TASK_CREATED", "Đánh giá thêm tác động của xử lý bất đồng bộ", "async_processing", 7, "An"),
        event("RISK_RAISED", "Chi phí API có thể tăng khi gọi LLM nhiều và số người dùng lớn", "llm_cost", 8, "Bình"),
    ], {
        "tasks": [task("Kiểm tra lại timeout configuration", 5, "Bình", "trước ngày 17/10/2026"),
                  task("Đánh giá thêm tác động của xử lý bất đồng bộ", 7)],
        "problems": [record("API phân tích transcript bị timeout với dữ liệu dài khoảng 30.000 từ", 1, 2)],
        "obstacles": [record("Lỗi timeout chặn kiểm thử các cuộc họp dài", 3)],
        "risks": [record("Hệ thống có thể timeout khi khách hàng thử transcript dài trong demo", 4),
                  record("Chi phí API có thể tăng khi gọi LLM nhiều và số người dùng lớn", 8)],
        "unfinalized_content": [record("Chưa chốt xử lý bất đồng bộ, cần đánh giá tác động", 6, 7)],
    }, [
        (2, 1, "SAME_TOPIC", "Bình xác nhận timeout xảy ra với transcript khoảng 30.000 từ."),
        (3, 1, "REFERS_TO", "Chi nêu ảnh hưởng trực tiếp của lỗi timeout lên kiểm thử."),
        (7, 6, "REFERS_TO", "An để ngỏ đề xuất bất đồng bộ để đánh giá thêm."),
    ]),
    # Exclude small talk, completed work, and the resolved newline bug from final active items.
    case(5, [
        event("TASK_COMPLETED", "Hoàn thành giao diện nhập transcript", "transcript_input", 5, "Bình", owner="Bình"),
        event("FEEDBACK", "Giao diện dễ hiểu nhưng nút Analyze khó nhìn", "analyze_button", 6, "Chi"),
        event("TASK_CREATED", "Chỉnh màu sắc và kích thước nút Analyze", "analyze_button", 7, "An", target="Bình", owner="Bình", deadline="trước ngày 19/10/2026"),
        event("PROBLEM_RAISED", "Nút Analyze không hoạt động khi transcript chứa xuống dòng", "analyze_newline", 11, "Chi"),
        event("PROBLEM_RESOLVED", "Đã sửa lỗi Analyze với ký tự xuống dòng", "analyze_newline", 12, "Bình"),
        event("PROBLEM_RESOLVED", "Kiểm thử lại xác nhận nút Analyze hoạt động bình thường", "analyze_newline", 13, "Chi"),
        event("PROBLEM_RESOLVED", "Xác nhận lỗi Analyze đã xử lý", "analyze_newline", 14, "An"),
        event("FEEDBACK", "Kết quả JSON hiển thị dài, người dùng phải cuộn nhiều", "results_display", 15, "Bình"),
        event("DECISION_PROPOSAL", "Chia kết quả thành tab theo nhóm thông tin", "results_display", 16, "Chi"),
        event("UNFINALIZED_CANDIDATE", "Chưa triển khai chia tab, tuần sau xem xét", "results_display", 17, "An"),
    ], {
        "tasks": [task("Chỉnh màu sắc và kích thước nút Analyze", 7, "Bình", "trước ngày 19/10/2026")],
        "feedback": [record("Giao diện dễ hiểu nhưng nút Analyze khó nhìn", 6),
                     record("Kết quả JSON hiển thị dài, người dùng phải cuộn nhiều", 15)],
        "unfinalized_content": [record("Chưa triển khai chia kết quả thành tab theo nhóm; tuần sau xem xét", 16, 17)],
    }, [
        (5, 4, "RESOLVES", "Bình cho biết đã sửa lỗi xuống dòng."),
        (6, 4, "RESOLVES", "Chi kiểm thử lại và xác nhận nút hoạt động."),
        (7, 4, "RESOLVES", "An xác nhận lỗi đã được xử lý."),
        (10, 9, "REFERS_TO", "An hoãn xem xét đề xuất chia tab sang tuần sau."),
    ]),
    # Tentative offers are not assigned tasks or a final platform choice.
    case(6, [
        event("DECISION_PROPOSAL", "Sử dụng Render để triển khai backend", "backend_platform", 2, "Bình"),
        event("PROBLEM_RAISED", "Backend trên Render không phản hồi, frontend báo 502 trong lần kiểm thử", "render_deployment", 3, "Chi"),
        event("FEEDBACK", "Render không ổn định trong lần kiểm thử", "render_deployment", 4, "An"),
        event("FEEDBACK", "Có thể cấu hình port sai, chưa chắc do Render", "render_deployment", 5, "Bình"),
        event("DECISION_PROPOSAL", "Chuyển sang Railway", "backend_platform", 6, "Chi"),
        event("FEEDBACK", "Railway có thể thuận tiện theo dõi deployment nhưng chưa thử thực tế", "backend_platform", 8, "Chi"),
        event("DECISION_PROPOSAL", "Giữ Render và sửa cấu hình", "backend_platform", 9, "Bình"),
        event("UNFINALIZED_CANDIDATE", "Chưa chọn nền tảng, muốn kiểm thử cả Render và Railway", "backend_platform", 12, "An"),
        event("UNFINALIZED_CANDIDATE", "Chưa phân công chính thức việc kiểm thử nền tảng", "platform_testing", 15, "An"),
        event("UNFINALIZED_CANDIDATE", "Chỉ quyết định nền tảng sau khi có kết quả kiểm thử", "backend_platform", 17, "An"),
    ], {
        "problems": [record("Backend trên Render không phản hồi, frontend báo 502 trong lần kiểm thử", 3)],
        "feedback": [record("Render không ổn định trong lần kiểm thử", 4),
                     record("Có thể cấu hình port sai, chưa chắc do Render", 5),
                     record("Railway có thể thuận tiện theo dõi deployment nhưng chưa thử thực tế", 8)],
        "unfinalized_content": [record("Chưa chọn Render hay Railway; chờ kết quả kiểm thử cả hai", 10, 12, 17),
                                record("Chưa phân công chính thức việc kiểm thử nền tảng", 13, 14, 15)],
    }, [
        (5, 1, "SAME_TOPIC", "Render và Railway là hai phương án triển khai backend."),
        (8, 5, "REFERS_TO", "An chưa chấp nhận Railway, muốn kiểm thử cả hai phương án."),
        (10, 8, "REFERS_TO", "Quyết định vẫn chờ kết quả kiểm thử."),
    ]),
    # Mixed MVP review: final decisions, active tasks, risks, and resolved history.
    case(7, [
        event("FEEDBACK", "Trích xuất Decision và Tasks khá tốt nhưng đôi khi nhầm Risks thành Problems", "classification", 3, "Chi"),
        event("TASK_CREATED", "Cải thiện khả năng phân loại", "classification", 4, "An"),
        event("DECISION_PROPOSAL", "Thêm bước validation bằng LLM thứ hai", "llm_validation", 5, "Bình"),
        event("RISK_RAISED", "Validation bằng LLM thứ hai có thể tăng thời gian xử lý và chi phí API", "llm_validation", 6, "Chi"),
        event("UNFINALIZED_CANDIDATE", "Chưa triển khai validation, cần đánh giá chi phí trước", "llm_validation", 7, "An"),
        event("TASK_CREATED", "Đánh giá chi phí validation bằng LLM thứ hai", "llm_validation", 7, "An"),
        event("DECISION_PROPOSAL", "Dùng model B cho transcript dài", "analysis_model", 9, "Chi"),
        event("DECISION_ACCEPTANCE", "Tiếp tục dùng model A cho MVP", "analysis_model", 12, "An"),
        event("UNFINALIZED_CANDIDATE", "Chuyển sang model B sẽ xem xét sau benchmark", "analysis_model", 12, "An"),
        event("TASK_CREATED", "Benchmark giữa model A và model B", "analysis_model", 13, "Bình", owner="Bình", deadline="trước ngày 20/10/2026"),
        event("PROBLEM_RAISED", "Frontend đôi lúc hiển thị timeout khi transcript dài", "frontend_timeout", 14, "Chi"),
        event("UNFINALIZED_CANDIDATE", "Chưa xác định nguyên nhân timeout, có thể từ backend hoặc proxy", "frontend_timeout", 16, "Bình"),
        event("TASK_CREATED", "Kiểm tra log backend và cấu hình timeout", "frontend_timeout", 17, "An", target="Bình", owner="Bình", deadline="trước ngày 18/10/2026"),
        event("REQUEST", "Tải kết quả dưới dạng JSON", "json_export", 19, "Chi"),
        event("DECISION_ACCEPTANCE", "Bổ sung xuất JSON vào MVP", "json_export", 20, "An"),
        event("TASK_CREATED", "Triển khai chức năng xuất JSON", "json_export", 21, "Chi", owner="Chi", deadline="trước ngày 22/10/2026"),
        event("RISK_RAISED", "Có thể lộ thông tin khi chia sẻ JSON chứa dữ liệu nhạy cảm", "json_export", 22, "Bình"),
        event("PROBLEM_RESOLVED", "Đã sửa lỗi hiển thị sai tên người nói", "speaker_display", 24, "Chi"),
        event("PROBLEM_RESOLVED", "Kiểm thử ba transcript chưa thấy lỗi tên người nói tái xuất hiện", "speaker_display", 26, "Chi"),
        event("PROBLEM_RESOLVED", "Xác nhận lỗi tên người nói không còn là vấn đề đang tồn tại", "speaker_display", 27, "An"),
        event("UNFINALIZED_CANDIDATE", "Chưa quyết định nhận audio trực tiếp, xem xét ở giai đoạn sau", "audio_input", 29, "An"),
    ], {
        "decisions": [record("Tiếp tục dùng model A cho MVP", 12), record("Bổ sung xuất JSON vào MVP", 20)],
        "tasks": [task("Cải thiện khả năng phân loại", 4),
                  task("Đánh giá chi phí validation bằng LLM thứ hai", 7),
                  task("Benchmark giữa model A và model B", 13, "Bình", "trước ngày 20/10/2026"),
                  task("Kiểm tra log backend và cấu hình timeout", 17, "Bình", "trước ngày 18/10/2026"),
                  task("Triển khai chức năng xuất JSON", 21, "Chi", "trước ngày 22/10/2026")],
        "problems": [record("Frontend đôi lúc hiển thị timeout khi transcript dài", 14)],
        "requests": [request("Tải kết quả dưới dạng JSON", 19, "Chi")],
        "feedback": [record("Trích xuất Decision và Tasks khá tốt nhưng đôi khi nhầm Risks thành Problems", 3)],
        "risks": [record("Validation bằng LLM thứ hai có thể tăng thời gian xử lý và chi phí API", 6),
                  record("Có thể lộ thông tin khi chia sẻ JSON chứa dữ liệu nhạy cảm", 22)],
        "unfinalized_content": [record("Chưa triển khai validation, cần đánh giá chi phí trước", 5, 7),
                                record("Chuyển sang model B sẽ xem xét sau benchmark", 9, 12),
                                record("Chưa xác định nguyên nhân timeout, có thể từ backend hoặc proxy", 16),
                                record("Chưa quyết định nhận audio trực tiếp, xem xét ở giai đoạn sau", 28, 29)],
    }, [
        (5, 3, "REFERS_TO", "An hoãn triển khai validation để đánh giá chi phí."),
        (9, 7, "REFERS_TO", "Đề xuất model B chờ benchmark; model A vẫn dùng cho MVP."),
        (13, 11, "REFERS_TO", "An giao kiểm tra log và timeout cho lỗi frontend đã nêu."),
        (15, 14, "ACCEPTS", "An chốt bổ sung yêu cầu xuất JSON vào MVP."),
        (19, 18, "REFERS_TO", "Chi xác nhận đã kiểm thử lại lỗi tên người nói."),
        (20, 18, "REFERS_TO", "An xác nhận không đưa lỗi đã sửa vào danh sách đang tồn tại."),
    ]),
]
