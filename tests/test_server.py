import asyncio

import pytest
from mcp.server.mcpserver.exceptions import ToolError

import server


def test_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {"get_price", "get_history", "analyze"}


def test_get_history_rejects_bad_days():
    with pytest.raises(ToolError, match = "1~250"):
        server.get_history("005930", 0)

def test_analyze_rejects_short_days():
    with pytest.raises(ToolError, match = "20~250"):
        server.analyze("005930", 10)

        