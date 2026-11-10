"""Offline tests for the FRED configuration layer. A fake client stands in for fredapi."""
import pandas as pd
import pytest

import fredcfg


class FakeFred:
    def get_series(self, sid, observation_start=None):
        return pd.Series([1.0, None, 3.0], index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]))

    def get_series_info(self, sid):
        return pd.Series({"title": "Fed assets", "units": "Millions", "frequency": "Weekly",
                          "seasonal_adjustment": "NSA", "last_updated": "2026-11-05"})

    def get_series_as_of_date(self, sid, date):
        return pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-08"]),
            "realtime_start": pd.to_datetime(["2024-01-05", "2024-02-01", "2024-01-12"]),
            "value": [10.0, 11.0, 20.0],
        })

    def get_series_first_release(self, sid):
        return pd.Series([10.0], index=pd.to_datetime(["2024-01-01"]))


def test_key_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    assert fredcfg.load_api_key(tmp_path / "missing.env") == "a" * 32


def test_key_from_env_file_when_environment_empty(monkeypatch, tmp_path):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    f = tmp_path / ".env"
    f.write_text('FRED_API_KEY="' + "b" * 32 + '"\n', encoding="utf-8")
    assert fredcfg.load_api_key(f) == "b" * 32


def test_no_key_means_csv_mode(monkeypatch, tmp_path):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    assert fredcfg.load_api_key(tmp_path / "nope.env") is None
    assert fredcfg.FredSource(api_key=None).mode == "csv"


def test_malformed_key_is_rejected_before_any_network_call():
    with pytest.raises(ValueError):
        fredcfg.FredSource(api_key="not-a-real-key")


def test_series_cleans_missing_values_and_names_the_series():
    s = fredcfg.FredSource(client=FakeFred()).series("WALCL")
    assert s.name == "WALCL" and list(s) == [1.0, 3.0]


def test_as_of_keeps_the_latest_vintage_per_date():
    s = fredcfg.FredSource(client=FakeFred()).as_of("WALCL", "2024-03-01")
    assert s.loc["2024-01-01"] == 11.0 and s.loc["2024-01-08"] == 20.0


def test_official_only_features_need_a_key():
    src = fredcfg.FredSource(api_key=None)
    for call in (lambda: src.info("WALCL"), lambda: src.search("x"),
                 lambda: src.as_of("WALCL", "2024-01-01"), lambda: src.first_release("WALCL")):
        with pytest.raises(fredcfg.NeedsApiKey):
            call()


def test_info_returns_metadata_with_a_client():
    assert fredcfg.FredSource(client=FakeFred()).info("WALCL")["title"] == "Fed assets"
