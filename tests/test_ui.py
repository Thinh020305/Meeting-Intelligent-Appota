from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

from tests.sample_transcripts.cases import CASES

UI = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"


def test_ui_submits_and_displays_evidence(monkeypatch):
    sample = CASES[0]
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json=sample["final"])

    monkeypatch.setattr(httpx, "post", post)
    app = AppTest.from_file(str(UI)).run()
    assert not app.exception
    app.text_area[0].set_value(sample["transcript"])
    app.button[0].click().run()
    assert not app.exception
    assert calls[0][1]["json"] == {"transcript": sample["transcript"]}
    assert any("seg_004" in text.value and "Tôi nhận thiết kế database schema" in text.value for text in app.text)
    assert any("owner: Chi" in caption.value for caption in app.caption)
    assert app.session_state.analysis[0] == sample["final"]


def test_ui_reports_connection_error(monkeypatch):
    def post(*args, **kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "post", post)
    app = AppTest.from_file(str(UI)).run()
    app.text_area[0].set_value("PM: Chốt A.")
    app.button[0].click().run()
    assert not app.exception
    assert "Không kết nối" in app.error[0].value


def test_ui_blank_input_does_not_call_api(monkeypatch):
    def post(*args, **kwargs):
        raise AssertionError("Blank input must not call API")

    monkeypatch.setattr(httpx, "post", post)
    app = AppTest.from_file(str(UI)).run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.error) == 1
