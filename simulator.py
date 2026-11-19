"""가상 틱·호가 데이터 생성기.

실제 거래소의 주문 단위 원본 데이터(틱·호가)는 외부로 내보낼 수 없다.
그래서 같은 구조의 가상 데이터를 만들어 "원본은 서버 안에만 두고 파생 지표만 내보내는"
Compute-to-Data 구조를 연습한다. 스푸핑(정답 라벨 포함)과 정상 대량 주문(헷갈리게 하는 잡음)을 섞는다.
"""
import itertools
import random

TICK = 100          # 호가 단위(원)
START_PRICE = 70_000


def _price_path(rng: random.Random, n_seconds: int) -> list[int]:
    """1초마다 한 틱씩 오르거나 내리거나 그대로인 매수 1호가 경로."""
    bids = [START_PRICE]
    for _ in range(n_seconds - 1):
        bids.append(bids[-1] + rng.choice([-TICK, 0, 0, 0, TICK]))
    return bids


def _order_events(oid, t, side, price, qty, end_type=None, lifetime=0.0) -> list[dict]:
    """주문 하나의 이벤트 목록: new, 그리고 선택적으로 cancel 또는 trade."""
    events = [{"ts": round(t, 3), "order_id": oid, "side": side, "type": "new", "price": price, "qty": qty}]
    if end_type:
        events.append({"ts": round(t + lifetime, 3), "order_id": oid, "side": side,
                       "type": end_type, "price": price, "qty": qty})
    return events


def simulate(ticker: str = "DEMO01", n_seconds: int = 3600, seed: int = 42,
             n_spoofs: int = 20, n_large: int = 20) -> dict:
    """가상 장중 데이터(기본 3600초 = 1시간)를 만든다. 같은 seed면 항상 같은 결과."""
    if n_seconds < 120:
        raise ValueError("n_seconds는 120 이상이어야 합니다.")
    rng = random.Random(seed)
    ids = (f"O{n:06d}" for n in itertools.count(1))
    bids = _price_path(rng, n_seconds)
    spreads = [rng.choice([1, 1, 1, 2]) for _ in range(n_seconds)]
    events: list[dict] = []
    big_orders: list[dict] = []   # 호가 잔량에 반영할 대량 주문 (side, 시작, 끝, 수량)
    spoofs: list[dict] = []

    # 1) 일반 주문: 초당 0~4건, 소량. 일부는 체결, 일부는 취소, 나머지는 대기.
    for t in range(n_seconds):
        for _ in range(rng.randint(0, 4)):
            side = rng.choice(["B", "S"])
            price = bids[t] if side == "B" else bids[t] + spreads[t] * TICK
            r = rng.random()
            if r < 0.3:
                end, life = "trade", rng.uniform(0.5, 10)
            elif r < 0.6:
                end, life = "cancel", rng.uniform(2, 30)
            else:
                end, life = None, 0.0
            events += _order_events(next(ids), t + rng.random(), side, price,
                                    rng.randint(10, 100), end, life)

    # 2) 스푸핑: 대량 주문을 냈다가 체결 전에 몇 초 안에 취소한다.
    for _ in range(n_spoofs):
        t0 = rng.uniform(60, n_seconds - 60)
        side = rng.choice(["B", "S"])
        qty = rng.randint(500, 3000)
        life = rng.uniform(1, 4)
        oid = next(ids)
        price = bids[int(t0)] if side == "B" else bids[int(t0)] + spreads[int(t0)] * TICK
        events += _order_events(oid, t0, side, price, qty, "cancel", life)
        big_orders.append({"side": side, "start": t0, "end": t0 + life, "qty": qty})
        spoofs.append({"order_id": oid, "side": side, "start": round(t0, 3), "end": round(t0 + life, 3)})

    # 3) 정상 대량 주문: 크기는 비슷하지만 대부분 체결되거나 오래 머문다(잡음).
    for _ in range(n_large):
        t0 = rng.uniform(60, n_seconds - 60)
        side = rng.choice(["B", "S"])
        qty = rng.randint(400, 3000)
        if rng.random() < 0.7:
            end, life = "trade", rng.uniform(1, 20)
        else:
            end, life = "cancel", rng.uniform(1, 30)
        price = bids[int(t0)] if side == "B" else bids[int(t0)] + spreads[int(t0)] * TICK
        events += _order_events(next(ids), t0, side, price, qty, end, life)
        big_orders.append({"side": side, "start": t0, "end": t0 + life, "qty": qty})

    events.sort(key=lambda e: e["ts"])

    # 4) 1초 단위 호가 스냅샷: 기본 잔량 + 그 순간 걸려 있는 대량 주문.
    quotes = []
    for t in range(n_seconds):
        bid_qty, ask_qty = rng.randint(500, 1500), rng.randint(500, 1500)
        for o in big_orders:
            if o["start"] <= t < o["end"]:
                if o["side"] == "B":
                    bid_qty += o["qty"]
                else:
                    ask_qty += o["qty"]
        quotes.append({"ts": t, "bid": bids[t], "ask": bids[t] + spreads[t] * TICK,
                       "bid_qty": bid_qty, "ask_qty": ask_qty})

    return {"ticker": ticker, "events": events, "quotes": quotes, "spoofs": spoofs}