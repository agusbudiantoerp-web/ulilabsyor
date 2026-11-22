from daily_signal_service import format_report
from daily_signal_telegram import _chunks


def test_report_mentions_no_trade_and_data_source():
    report=format_report({"counts":{"scanned":2,"success":0,"failed":2,"buy_candidate":0,"watch":0,"no_trade":0},"results":[],"errors":[{"market":"IDX","symbol":"BBCA","error":"network"}]})
    assert "AI EQUITY RESEARCH" in report
    assert "Tidak ada saham" in report
    assert "Yahoo Finance" in report
    assert "BBCA" in report


def test_report_includes_candidate_risk_levels():
    candidate={"market":"IDX","ticker":"BBCA.JK","signal":"BUY_CANDIDATE","score":80,"close":9000,"currency":"IDR","entry_low":8910,"entry_high":9090,"stop_loss":8700,"target":9540,"reward_risk":1.8,"bar_date":"2026-11-19","rsi14":60,"relative_volume":1.3,"warnings":[]}
    report=format_report({"counts":{"scanned":1,"success":1,"failed":0,"buy_candidate":1,"watch":0,"no_trade":0},"results":[candidate],"errors":[]})
    assert "BBCA.JK" in report
    assert "Stop" in report and "Target" in report
    assert "1.80" in report


def test_telegram_report_splits_long_messages():
    chunks=_chunks("x"*8500)
    assert len(chunks)==3
    assert all(len(chunk)<=3900 for chunk in chunks)


def test_report_always_shows_tpia_even_when_no_trade():
    tpia = {
        "market": "IDX", "ticker": "TPIA.JK", "signal": "NO_TRADE", "score": 15,
        "close": 1155, "currency": "IDR", "bar_date": "2026-11-20",
        "rsi14": 32.93, "relative_volume": 0.45, "return5_pct": -12.17,
        "entry_low": 1143.45, "entry_high": 1166.55, "stop_loss": 1020.90,
        "target": 1396.38, "reward_risk": 1.8, "warnings": [],
    }
    report = format_report({
        "counts": {"scanned": 1, "success": 1, "failed": 0, "buy_candidate": 0, "watch": 0, "no_trade": 1},
        "results": [tpia], "errors": [],
    })
    assert "PANTAUAN KHUSUS TPIA" in report
    assert "NO_TRADE" in report
    assert "1,155.00 IDR" in report
    assert "2026-11-20" in report
    assert "-12.17%" in report
