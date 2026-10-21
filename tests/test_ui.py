"""Native Streamlit execution tests; browser acceptance is recorded separately."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize(
    "name",
    [
        "Overview",
        "Knowledge Assistant",
        "Agent Workspace",
        "Verification Results",
        "Knowledge Sources",
        "Execution History",
        "Architecture & Methodology",
    ],
)
def test_all_pages_render(name, tmp_path, monkeypatch):
    monkeypatch.setenv("EVENTOPS_DATABASE_URL", "sqlite:///" + str(tmp_path / "ui.db"))
    monkeypatch.setenv("GEMINI_ENABLED", "false")
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
    # AppTest's public switch_page accepts file pages; this application uses native callable pages.
    at._page_hash = next(key for key, page in at._registered_pages.items() if page["page_name"] == name)
    at.run(timeout=30)
    assert not at.exception
    assert at.title


def test_password_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_PASSWORD", "test-password")
    monkeypatch.setenv("EVENTOPS_DATABASE_URL", "sqlite:///" + str(tmp_path / "ui.db"))
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert at.text_input[0].label == "Workspace password"
    at.text_input[0].set_value("wrong")
    at.button[0].click().run()
    assert at.error
    at.text_input[0].set_value("test-password")
    at.button[0].click().run()
    assert not at.exception
    assert at.title[0].value == "Traceable event operations."


def test_hosted_gate_requires_password(monkeypatch):
    monkeypatch.setenv("PUBLIC_DEMO", "true")
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert at.error and "password" in at.error[0].value
