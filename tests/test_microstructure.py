import pytest

from microstructure import detect_spoofing, load_dataset, window_metrics


def make_data():
    quotes = [{"ts": t, "bid": 100, "ask": 200, "bid_qty": 300, "ask_qty": 100} for t in range(120)]
    events = [
        {"ts": 1.0, "order_id": "A", "side": "B", "type": "new", "price": 100, "qty": 10},
        {"ts": 2.0, "order_id": "B", "side": "S", "type": "new", "price": 200, "qty": 10},
        {"ts": 3.0, "order_id": "C", "side": "B", "type": "new", "price": 100, "qty": 1000},
        {"ts": 4.0, "order_id": "C", "side": "B", "type": "cancel", "price": 100, "qty": 1000},
        {"ts": 70.0, "order_id": "A", "side": "B", "type": "trade", "price": 100, "qty": 10},
    ]
    return {"quotes": quotes, "events": events}


def test_detect_spoofing():
    alerts = detect_spoofing(make_data())
    assert [a["order_id"] for a in alerts] == ["C"]


def test_window_metrics():
    rows = window_metrics(make_data(), 60)
    assert len(rows) == 2
    w0, w1 = rows
    assert (w0["n_new"], w0["n_cancel"], w0["n_events"]) == (3, 1, 4)
    assert w0["cancel_ratio"] == 0.333
    assert w0["avg_spread"] == 100.0
    assert w0["avg_obi"] == 0.5
    assert w0["spoof_alerts"] == 1
    assert (w1["n_trade"], w1["cancel_ratio"], w1["spoof_alerts"]) == (1, 0.0, 0)


def test_rows_have_no_order_id():
    rows = window_metrics(load_dataset("DEMO01"), 60)
    assert all("order_id" not in r for r in rows)


def test_unknown_dataset_raises():
    with pytest.raises(ValueError):
        load_dataset("XXXX")