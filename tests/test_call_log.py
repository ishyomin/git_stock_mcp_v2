import json

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from call_log import logged


def read_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_success_is_logged(temp_log):
    @logged
    def add(a: int, b: int = 10) -> int:
        return a + b

    assert add(1) == 11
    rec = read_records(temp_log)[0]
    assert rec["tool"] == "add"
    assert rec["args"] == {"a": 1, "b": 10}
    assert rec["ok"] is True


def test_value_error_becomes_tool_error(temp_log):
    @logged
    def bad() -> None:
        raise ValueError("잘못된 입력")

    with pytest.raises(ToolError, match="잘못된 입력"):
        bad()
    rec = read_records(temp_log)[0]
    assert rec["ok"] is False
    assert rec["error"] == "잘못된 입력"


def test_unexpected_error_is_hidden(temp_log):
    @logged
    def crash() -> None:
        raise RuntimeError("secret detail")

    with pytest.raises(ToolError) as exc_info:
        crash()
    assert "secret detail" not in str(exc_info.value)
    assert "RuntimeError" in read_records(temp_log)[0]["error"]