import pytest

from stock import pct_change, period_return, to_yahoo_candidates

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

