"""주가 조회와 계산 로직. MCP와 분리해 네트워크 없이 테스트할 수 있게 한다."""
from datetime import date, timedelta
import math
import  statistics
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

def moving_average(values: list[float], window: int) -> float:
    """마지막 window개 값의 평균."""
    if window < 1 or window > len(values):
        raise ValueError(f"window는 1~{len(values)} 사이여야 합니다.")
    return round(sum(values[-window:]) / window, 2)


def daily_returns(closes: list[float]) -> list[float]:
    """이웃한 종가 사이의 일별 등락률(%) 목록."""
    if len(closes) < 2:
        raise ValueError("일별 수익률을 계산하려면 종가가 2개 이상 필요합니다.")
    return [pct_change(prev, cur) for prev, cur in zip(closes, closes[1:])]


def volatility(closes: list[float]) -> float:
    """일별 수익률의 표본 표준편차(%)."""
    returns = daily_returns(closes)
    if len(returns) < 2:
        raise ValueError("변동성을 계산하려면 종가가 3개 이상 필요합니다.")
    return round(statistics.stdev(returns), 2)


def max_drawdown(closes: list[float]) -> float:
    """기간 중 고점 대비 최대 하락률(%). 하락이 없으면 0.0."""
    if not closes:
        raise ValueError("종가가 비어 있습니다.")
    peak = closes[0]
    mdd = 0.0
    for c in closes:
        peak = max(peak, c)
        mdd = min(mdd, (c - peak) / peak * 100)
    return round(mdd, 2)


def analyze(ticker: str, days: int = 60) -> dict:
    """이동평균·추세·변동성·최대 낙폭을 한 번에 계산한다."""
    symbol, rows = fetch_history(ticker, days)
    closes = [r["close"] for r in rows]
    if len(closes) < 20:
        raise ValueError("분석하려면 거래일이 20일 이상 필요합니다.")

    ma5 = moving_average(closes, 5)
    ma20 = moving_average(closes, 20)
    if ma5 > ma20:
        trend = "상승"
    elif ma5 < ma20:
        trend = "하락"
    else:
        trend = "보합"
    vol = volatility(closes)

    return {
        "symbol": symbol,
        "days": len(closes),
        "start_date": rows[0]["date"],
        "end_date": rows[-1]["date"],
        "last_close": closes[-1],
        "ma5": ma5,
        "ma20": ma20,
        "trend": trend,
        "period_return_pct": period_return(closes),
        "daily_volatility_pct": vol,
        "annual_volatility_pct": round(vol * math.sqrt(252), 2),
        "max_drawdown_pct": max_drawdown(closes),
    }