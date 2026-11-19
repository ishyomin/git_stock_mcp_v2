"""원본 틱·호가에서 미시구조 지표를 계산하고 스푸핑 의심 주문을 찾는다.

이 파일의 결과에는 order_id 같은 원본 정보가 들어 있을 수 있다.
그래서 서버는 이 결과를 바로 내보내지 않고 policy.py를 거친 것만 내보낸다.
"""
import functools
import math
import statistics

from simulator import simulate

DATASETS = {"DEMO01": 42, "DEMO02": 7}   # 가상 종목 → seed


@functools.lru_cache(maxsize=None)
def load_dataset(ticker: str) -> dict:
    """가상 종목 데이터를 한 번만 만들고 재사용한다(원본 보관소 역할)."""
    if ticker not in DATASETS:
        raise ValueError(f"가상 종목은 {', '.join(DATASETS)}만 있습니다.")
    return simulate(ticker, seed=DATASETS[ticker])


def detect_spoofing(data: dict, qty_mult: float = 10.0, max_life: float = 5.0) -> list[dict]:
    """수량이 중앙값의 qty_mult배 이상이고 max_life초 안에 취소된 주문을 찾는다."""
    new = {e["order_id"]: e for e in data["events"] if e["type"] == "new"}
    median_qty = statistics.median(e["qty"] for e in new.values())
    alerts = []
    for e in data["events"]:
        if e["type"] != "cancel":
            continue
        order = new[e["order_id"]]
        life = e["ts"] - order["ts"]
        if order["qty"] >= qty_mult * median_qty and life <= max_life:
            alerts.append({"order_id": e["order_id"], "side": order["side"],
                           "start": order["ts"], "end": e["ts"], "qty": order["qty"]})
    return alerts


def window_metrics(data: dict, window_sec: int = 60) -> list[dict]:
    """window_sec초 단위로 주문 건수, 취소율, 스프레드, OBI, 스푸핑 의심 건수를 집계한다."""
    n_windows = math.ceil(len(data["quotes"]) / window_sec)
    counts = [{"new": 0, "cancel": 0, "trade": 0} for _ in range(n_windows)]
    for e in data["events"]:
        w = int(e["ts"] // window_sec)
        if w < n_windows:
            counts[w][e["type"]] += 1

    alerts = [0] * n_windows
    for a in detect_spoofing(data):
        w = int(a["start"] // window_sec)
        if w < n_windows:
            alerts[w] += 1

    rows = []
    for w in range(n_windows):
        qs = data["quotes"][w * window_sec:(w + 1) * window_sec]
        obis = [(q["bid_qty"] - q["ask_qty"]) / (q["bid_qty"] + q["ask_qty"]) for q in qs]
        c = counts[w]
        rows.append({
            "start_sec": w * window_sec,
            "n_events": c["new"] + c["cancel"] + c["trade"],
            "n_new": c["new"],
            "n_cancel": c["cancel"],
            "n_trade": c["trade"],
            "cancel_ratio": round(c["cancel"] / c["new"], 3) if c["new"] else 0.0,
            "avg_spread": round(statistics.mean(q["ask"] - q["bid"] for q in qs), 1),
            "avg_obi": round(statistics.mean(obis), 3),
            "max_abs_obi": round(max(abs(x) for x in obis), 3),
            "spoof_alerts": alerts[w],
        })
    return rows