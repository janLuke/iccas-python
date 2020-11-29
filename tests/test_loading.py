#!/usr/bin/env python

"""Tests for `iccas` package."""
from pathlib import Path

import iccas
import pandas as pd

SAMPLE_DATE = "2020-09-29"
SAMPLE_DATETIME = pd.Timestamp(2020, 9, 29, 11, 0)


def test_get(tmp_path: Path):
    d = iccas.get(cache_dir=tmp_path)
    assert isinstance(d, pd.DataFrame)
    assert isinstance(d.index, pd.DatetimeIndex)


def test_get_by_date(tmp_path: Path):
    d = iccas.get_by_date(SAMPLE_DATE, cache_dir=tmp_path)
    assert isinstance(d, pd.DataFrame)
    assert d.index.name == "age_group"
    assert d.attrs["date"] == SAMPLE_DATETIME


def test_get_by_date_keeping_date_column(tmp_path: Path):
    d = iccas.get_by_date(SAMPLE_DATE, cache_dir=tmp_path, keep_date=True)
    assert isinstance(d, pd.DataFrame)
    assert isinstance(d.index, pd.MultiIndex)
    assert isinstance(d.index.levels[0], pd.DatetimeIndex)
    assert d.index.levels[0].name == "date"
    assert d.index.levels[1].name == "age_group"
