import pandas as pd
import pytest

import iccas
from iccas.processing import nullify_series_local_bumps

# A replacement for NaN such that (NA == NA)
NA = -1


@pytest.fixture(scope="session")
def _data(tmpdir_factory):
    cache_dir = tmpdir_factory.mktemp("data")
    return iccas.get(cache_dir=cache_dir).head(10)


@pytest.fixture()
def data(_data):
    return _data.copy()


@pytest.mark.parametrize('freq', [1, 7, 'M'])
def test_resample(data, freq):
    hour = 18
    r = iccas.resample(data, freq=1)
    expected_index = pd.date_range(
        data.index[0].replace(hour=hour, minute=0),
        data.index[-1].replace(hour=hour, minute=0),
        freq="D",
    )
    assert (r.index == expected_index).all(axis=None)
    assert not r.isna().any(axis=None)


@pytest.mark.parametrize(
    "x, expected",
    [
        ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
        ([1, 2, 5, 6, 4, 3], [1, 2, NA, NA, NA, 3]),
        ([7, 6, 1, 2, 4, 6, 5], [NA, NA, 1, 2, 4, NA, 5]),
        ([5, 3, 4, 4, 1], [NA, NA, NA, NA, 1]),
        ([1] * 5, [1] * 5),
    ],
)
def test_nullify_series_local_bumps(x, expected):
    actual = nullify_series_local_bumps(pd.Series(x)).fillna(NA).tolist()
    assert actual == expected
