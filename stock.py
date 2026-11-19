"""주가 조회와 계산 로직. MCP와 분리해 네트워크 없이 테스트할 수 있게 한다."""
from datetime import date, timedelta

import yfinance as yf


def to_yahoo_candidates(ticker: str) -> list[str]:
    """사용자 입력 티커를 야후 파이낸스 심볼 후보 목록으로 바꾼다."""
    t = ticker.strip().upper()
    if t.isdigit() and len(t) == 6:
        return [f"{t}.KS", f"{t}.KQ"]
    return [t]


def pct_change(old: float, new: float) -> float:
    """old 대비 new의 등락률(%)."""
    if old == 0:
        raise ValueError("기준값이 0이라 등락률을 계산할 수 없습니다.")
    return round((new - old) / old * 100, 2)


def period_return(closes: list[float]) -> float:
    """기간 첫 종가 대비 마지막 종가 수익률(%)."""
    if len(closes) < 2:
        raise ValueError("수익률을 계산하려면 종가가 2개 이상 필요합니다.")
    return pct_change(closes[0], closes[-1])


def fetch_history(ticker: str, days: int = 20) -> tuple[str, list[dict]]:
    """최근 days 거래일의 시세. (실제 찾은 심볼, 행 목록)을 돌려준다."""
    if days < 1:
        raise ValueError("days는 1 이상이어야 합니다.")
    start = date.today() - timedelta(days=days * 2 + 10)

    for symbol in to_yahoo_candidates(ticker):
        df = yf.Ticker(symbol).history(start=start.isoformat())
        if df.empty:
            continue
        rows = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(r["Open"]), 2),
                "high": round(float(r["High"]), 2),
                "low": round(float(r["Low"]), 2),
                "close": round(float(r["Close"]), 2),
                "volume": int(r["Volume"]),
            }
            for idx, r in df.tail(days).iterrows()
        ]
        return symbol, rows

    raise ValueError(f"'{ticker}' 종목을 찾을 수 없습니다.")


def get_price(ticker: str) -> dict:
    """최신 종가와 전일 대비 등락률."""
    symbol, rows = fetch_history(ticker, days=2)
    last = rows[-1]
    result = {"symbol": symbol, "date": last["date"], "close": last["close"]}
    if len(rows) >= 2:
        prev = rows[-2]["close"]
        result["prev_close"] = prev
        result["change_pct"] = pct_change(prev, last["close"])
    return result