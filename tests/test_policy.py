import pytest

from policy import apply_policy, check_window


def row(n_events, **extra):
    return {"start_sec": 0, "n_events": n_events, **extra}


def test_window_too_small_raises():
    with pytest.raises(ValueError, match="60"):
        check_window(30)


def test_sparse_windows_suppressed():
    result = apply_policy([row(5), row(20), row(100)])
    assert len(result["rows"]) == 2
    assert result["suppressed_windows"] == 1


def test_rows_truncated():
    result = apply_policy([row(50) for _ in range(250)])
    assert len(result["rows"]) == 200
    assert result["truncated"] is True


def test_forbidden_key_blocked():
    with pytest.raises(PermissionError):
        apply_policy([row(50, order_id="O000001")])