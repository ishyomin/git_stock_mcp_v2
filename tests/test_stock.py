import pytest

from stock import (
    daily_returns,
    max_drawdown,
    moving_average,
    pct_change,
    period_return,
    to_yahoo_candidates,
    volatility,
)
def test_korean_ticker_candidates():
    assert to_yahoo_candidates("005930") == ["005930.KS", "005930.KQ"]

def test_us_ticker_strip_and_upper():
    assert to_yahoo_candidates("appl") == ["APPL"]

def test_suffix_kept():
    assert to_yahoo_candidates("005930.KS")==["005930.KS"]

def test_pct_change():
    assert pct_change(100, 110) == 10.0
    assert pct_change(200, 150) == -25.0
 
def test_pct_zero_raises():
    with pytest.raises(ValueError):
        pct_change(0, 10)

def test_period_return():
    assert period_return([100, 90, 120]) == 20.0

def test_period_return_too_short_raises():
    with pytest.raises(ValueError):
        period_return([100])

def test_moving_average():
    assert moving_average([1, 2, 3, 4, 5], 3) == 4.0


def test_moving_average_bad_window_raises():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 5)


def test_daily_returns():
    assert daily_returns([100, 110, 99]) == [10.0, -10.0]


def test_volatility():
    assert volatility([100, 110, 99]) == 14.14
    assert volatility([100, 100, 100]) == 0.0


def test_volatility_too_short_raises():
    with pytest.raises(ValueError):
        volatility([100, 110])


def test_max_drawdown():
    assert max_drawdown([100, 120, 90, 130, 117]) == -25.0
    assert max_drawdown([1, 2, 3]) == 0.0