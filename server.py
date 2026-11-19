"""주가 조회 MCP 서버, stock.py의 함수를 MCP 도구로 등록
주의:sdtio 방식에서는 sdtout이 통신채널이라 print() 쓰면 안됨"""

from mcp.server.mcpserver import MCPServer

import stock

mcp = MCPServer("stock-mcp-v2")

@mcp.tool()
def  get_price(ticker: str) -> dict:
    """ 종목의 최신 종가와 전일 대비 등락률(%)를 조회
    Args:
        ticker (str): 종목코드(티커). 한국 주식은 6자리 숫자, 미국 주식은 티커(e.g. AAPL)"""
    return stock.get_price(ticker)

@mcp.tool()
def get_history(ticker: str, days: int = 20) -> dict:
    """ 종목의 최근 n일간 종가와 전일 대비 등락률(%)를 조회
    Args:
        ticker (str): 종목코드(티커). 한국 주식은 6자리 숫자, 미국 주식은 티커(e.g. AAPL)
        days (int): 조회할 일수. 기본값 20일"""
    if not 1 <= days <= 365:
        raise ValueError("days must be between 1~250")
    symbol, rows = stock.fetch_history(ticker, days)
    result = {"symbol": symbol, "days": len(rows), "rows": rows}
    closes = [r["close"] for r in rows ]
    if len(closes) >= 2:
        result["period_return_pct"]=stock.period_return(closes)
    return result

if __name__ == "__main__":
    mcp.run()