import pytest

from simulator import simulate


def test_same_seed_same_data():
    assert simulate(seed=7, n_seconds=300) == simulate(seed=7, n_seconds=300)


def test_different_seed_differs():
    assert simulate(seed=1, n_seconds=300) != simulate(seed=2, n_seconds=300)


def test_too_short_raises():
    with pytest.raises(ValueError):
        simulate(n_seconds=60)


def test_events_sorted_by_time():
    ev = simulate(n_seconds=300)["events"]
    assert all(a["ts"] <= b["ts"] for a, b in zip(ev, ev[1:]))


def test_quotes_one_per_second():
    q = simulate(n_seconds=300)["quotes"]
    assert len(q) == 300
    assert all(x["ask"] > x["bid"] for x in q)


def test_cancel_and_trade_follow_new():
    new_ts = {}
    for e in simulate(n_seconds=300)["events"]:
        if e["type"] == "new":
            new_ts[e["order_id"]] = e["ts"]
        else:
            assert e["order_id"] in new_ts
            assert e["ts"] >= new_ts[e["order_id"]]


def test_spoofs_are_big_fast_cancels():
    data = simulate(n_seconds=600, n_spoofs=5)
    assert len(data["spoofs"]) == 5
    by_id = {}
    for e in data["events"]:
        by_id.setdefault(e["order_id"], []).append(e)
    for s in data["spoofs"]:
        events = by_id[s["order_id"]]
        assert [e["type"] for e in events] == ["new", "cancel"]
        assert events[0]["qty"] >= 500
        assert s["end"] - s["start"] <= 4