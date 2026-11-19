import pytest

import call_log


@pytest.fixture(autouse=True)
def temp_log(tmp_path, monkeypatch):
    """모든 테스트에서 로그를 임시 파일에 쓰게 한다."""
    path = tmp_path / "calls.jsonl"
    monkeypatch.setattr(call_log, "LOG_PATH", path)
    return path