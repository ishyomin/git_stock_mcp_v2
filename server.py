"""주가 조회 MCP 서버. stock.py의 함수를 MCP 도구로 등록한다.

주의: stdio 방식에서는 stdout이 통신 채널이라 print()를 쓰면 안 된다.
"""
from mcp.server.mcpserver import MCPServer
from call_log import logged

import stock
import microstructure
import policy
mcp = MCPServer("stock-mcp-v2")


@mcp.tool()
@logged
def get_price(ticker: str) -> dict:
    """종목의 최신 종가와 전일 대비 등락률(%)을 조회한다.

    Args:
        ticker: 종목 코드. 한국 주식은 6자리 숫자(예: 005930), 미국 주식은 티커(예: AAPL).
    """
    return stock.get_price(ticker)


@mcp.tool()
@logged
def get_history(ticker: str, days: int = 20) -> dict:
    """최근 N 거래일의 일별 시세(시가·고가·저가·종가·거래량)와 기간 수익률(%)을 조회한다.

    Args:
        ticker: 종목 코드. 한국 주식은 6자리 숫자(예: 005930), 미국 주식은 티커(예: AAPL).
        days: 조회할 거래일 수(1~250). 기본 20.
    """
    if not 1 <= days <= 250:
        raise ValueError("days는 1~250 사이여야 합니다.")
    symbol, rows = stock.fetch_history(ticker, days)
    result = {"symbol": symbol, "days": len(rows), "rows": rows}
    closes = [r["close"] for r in rows]
    if len(closes) >= 2:
        result["period_return_pct"] = stock.period_return(closes)
    return result

@mcp.tool()
@logged
def analyze(ticker: str, days: int = 60) -> dict:
    """최근 N 거래일의 이동평균·추세·변동성·최대 낙폭을 조사한다. 거래일이 20일 미만이면 ValueError를 발생시킨다.
    5일, 20일 이동평균과 추세(상승, 하락 보합), 기간 수익률, 일별/연환산 변동성, 최대 낙폭(MDD)를 계산. 단위 %
    Args:
        ticker: 종목 코드. 한국 주식은 6자리 숫자(예: 005930), 미국 주식은 티커(예: AAPL).
        days: 조회할 거래일 수(20~250). 기본 60.
    """
    if not 20 <= days <= 250:
        raise ValueError("days는 20~250 사이여야 합니다.")
    return stock.analyze(ticker, days)

@mcp.tool()
@logged
def market_microstructure(ticker: str = "DEMO01", window_sec: int = 60) -> dict:
    """가상 종목의 시장 미시구조 지표를 구간별로 조회한다.

    원본 틱·호가(주문번호 포함)는 서버 밖으로 내보내지 않고, 반출 정책을 통과한
    집계 지표만 제공한다(Compute-to-Data). 이벤트 20건 미만 구간은 숨긴다.

    지표: n_new/n_cancel/n_trade(건수), cancel_ratio(취소/신규),
    avg_spread(원), avg_obi·max_abs_obi(호가 불균형, -1~1, +면 매수 우위),
    spoof_alerts(스푸핑 의심 주문 수. 확정이 아니라 추가 조사 대상).

    Args:
        ticker: 가상 종목 코드(DEMO01, DEMO02).
        window_sec: 집계 구간(초). 60~3600.
    """
    policy.check_window(window_sec)
    data = microstructure.load_dataset(ticker.strip().upper())
    rows = microstructure.window_metrics(data, window_sec)
    return policy.apply_policy(rows)

if __name__ == "__main__":
    mcp.run()