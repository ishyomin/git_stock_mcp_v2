import asyncio
import pytest
import server

def test_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {"get_price", "get_history"}

def test_get_history_rejects_bad_days():
    with pytest.raises(ValueError):
        server.get_history("005930", 0)