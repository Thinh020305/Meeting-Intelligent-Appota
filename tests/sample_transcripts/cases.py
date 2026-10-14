"""Ten golden cases from section 8 of the specification, with mocked stage outputs.

These are fixtures, not an alternative extraction engine or production fallback.
"""

GROUPS = ("decisions", "tasks", "problems", "requests", "obstacles", "feedback", "unfinalized_content", "risks")


def record(content, *segments, **fields):
    return {"content": content, **fields, "evidence_segment_ids": list(segments)}


def event(kind, content, subject, segment, actor=None, **fields):
    return {"event_type": kind, "content": content, "subject": subject,
            "actor": actor, "target": None, "owner": None, "deadline": None,
            "evidence_segment_ids": [segment], **fields}


def case(number, transcript, events, final, relations=(), topics=None):
    events = [{"event_id": f"evt_{i:03}", "order": i, **e} for i, e in enumerate(events, 1)]
    topics = topics or [list(range(1, len(events) + 1))]
    threads = [{"thread_id": f"thread_{i:03}", "topic": events[ids[0]-1]["subject"],
                "event_ids": [f"evt_{j:03}" for j in ids]} for i, ids in enumerate(topics, 1)]
    relationships = [{"from_event": f"evt_{a:03}", "to_event": f"evt_{b:03}",
                      "relation": rel, "reason": reason} for a, b, rel, reason in relations]
    return {"id": f"{number:02}", "transcript": transcript,
            "extraction": {"candidate_events": events},
            "relationship": {"threads": threads, "relationships": relationships},
            "final": {group: final.get(group, []) for group in GROUPS}}


CASES = [
    case(1, "seg_001 PM: Chốt dùng phương án A.", [
        event("DECISION_ACCEPTANCE", "Sử dụng phương án A", "phuong_an", "seg_001", "PM"),
    ], {"decisions": [record("Sử dụng phương án A", "seg_001")]}),
    case(2, "seg_001 Nam: Tôi đề xuất dùng Stripe.\nseg_002 Minh: Tôi đề xuất dùng PayOS.\nseg_003 PM: Ok, chốt PayOS.", [
        event("DECISION_PROPOSAL", "Sử dụng Stripe", "payment_provider", "seg_001", "Nam"),
        event("DECISION_PROPOSAL", "Sử dụng PayOS", "payment_provider", "seg_002", "Minh"),
        event("DECISION_ACCEPTANCE", "Sử dụng PayOS", "payment_provider", "seg_003", "PM"),
    ], {"decisions": [record("Sử dụng PayOS", "seg_003")]}, [
        (2, 1, "SAME_TOPIC", "Stripe và PayOS là hai lựa chọn cổng thanh toán."),
        (3, 2, "ACCEPTS", "PM nói 'Ok, chốt PayOS', chấp nhận đề xuất PayOS."),
    ]),
    case(3, "seg_001 Nam: Tôi đề xuất dùng Stripe.\nseg_002 Minh: PayOS cũng là một lựa chọn.\nseg_003 PM: Để mai quyết định.", [
        event("DECISION_PROPOSAL", "Sử dụng Stripe", "payment_provider", "seg_001", "Nam"),
        event("DECISION_PROPOSAL", "Sử dụng PayOS", "payment_provider", "seg_002", "Minh"),
        event("UNFINALIZED_CANDIDATE", "Để mai quyết định cổng thanh toán", "payment_provider", "seg_003", "PM"),
    ], {"unfinalized_content": [record("Chưa thống nhất Stripe hay PayOS", "seg_001", "seg_002", "seg_003")]}),
    case(4, "seg_001 PM: Nam hoàn thành API trước thứ Sáu nhé.", [
        event("TASK_CREATED", "Hoàn thành API", "api", "seg_001", "PM", owner="Nam", target="Nam", deadline="thứ Sáu"),
    ], {"tasks": [record("Hoàn thành API", "seg_001", owner="Nam", deadline="thứ Sáu")]}),
    case(5, "seg_001 PM: Cần hoàn thành API.", [
        event("TASK_CREATED", "Hoàn thành API", "api", "seg_001", "PM"),
    ], {"tasks": [record("Hoàn thành API", "seg_001", owner=None, deadline=None)]}),
    case(6, "seg_001 Nam: API login đang lỗi.", [
        event("PROBLEM_RAISED", "API login đang lỗi", "login_api", "seg_001", "Nam"),
    ], {"problems": [record("API login đang lỗi", "seg_001")]}),
    case(7, "seg_001 PM: Nam deploy production hôm nay nhé.\nseg_002 Nam: API đang lỗi nên hiện tại em chưa deploy được.", [
        event("TASK_CREATED", "Deploy production", "production_deployment", "seg_001", "PM", owner="Nam", target="Nam", deadline="hôm nay"),
        event("PROBLEM_RAISED", "API đang lỗi", "production_deployment", "seg_002", "Nam"),
        event("OBSTACLE_RAISED", "API lỗi đang cản deploy", "production_deployment", "seg_002", "Nam"),
    ], {"tasks": [record("Deploy production", "seg_001", owner="Nam", deadline="hôm nay")],
        "problems": [record("API đang lỗi", "seg_002")],
        "obstacles": [record("API lỗi đang cản deploy", "seg_002")]}, [
        (3, 1, "BLOCKS", "Nam nói API lỗi nên chưa deploy được."),
    ]),
    case(8, "seg_001 Khách hàng phản hồi giao diện hiện tại khó sử dụng.\nseg_002 Khách hàng yêu cầu đổi giao diện trang thanh toán.", [
        event("FEEDBACK", "Giao diện hiện tại khó sử dụng", "ui", "seg_001"),
        event("REQUEST", "Đổi giao diện trang thanh toán", "payment_ui", "seg_002", "Khách hàng"),
    ], {"feedback": [record("Giao diện hiện tại khó sử dụng", "seg_001")],
        "requests": [record("Đổi giao diện trang thanh toán", "seg_002", requester="Khách hàng", target=None)]}, topics=[[1], [2]]),
    case(9, "seg_001 Nam: Nếu traffic tăng mạnh khi launch thì server có thể quá tải.", [
        event("RISK_RAISED", "Server có thể quá tải khi traffic tăng mạnh lúc launch", "server_capacity", "seg_001", "Nam"),
    ], {"risks": [record("Server có thể quá tải khi traffic tăng mạnh lúc launch", "seg_001")]}),
    case(10, "seg_001 Nam: Login API đang lỗi.\nseg_002 Nam: Login API đã fix xong rồi.", [
        event("PROBLEM_RAISED", "Login API đang lỗi", "login_api", "seg_001", "Nam"),
        event("PROBLEM_RESOLVED", "Login API đã fix xong", "login_api", "seg_002", "Nam"),
    ], {}, [(2, 1, "RESOLVES", "Nam xác nhận Login API đã fix xong.")]),
]
