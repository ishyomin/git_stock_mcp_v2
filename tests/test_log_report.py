from log_report import read_logs, summarize


def test_read_logs_missing_file(tmp_path):
    assert read_logs(tmp_path / "none.jsonl") == []


def test_summarize():
    records = [
        {"tool": "get_price", "ok": True, "elapsed_ms": 100.0},
        {"tool": "get_price", "ok": False, "elapsed_ms": 300.0},
        {"tool": "analyze", "ok": True, "elapsed_ms": 50.0},
    ]
    assert summarize(records) == {
        "get_price": {"calls": 2, "errors": 1, "error_rate_pct": 50.0, "avg_ms": 200.0},
        "analyze": {"calls": 1, "errors": 0, "error_rate_pct": 0.0, "avg_ms": 50.0},
    }