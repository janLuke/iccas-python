import re
from typing import Union

import numpy as np
import pandas as pd
from pandas.core.dtypes.common import is_integer_dtype

from iccas.queries import cols, only_counts
from iccas.types import PandasObj


def reindex_by_interpolating(
    data: PandasObj,
    new_index: pd.DatetimeIndex,
    preserve_ints: bool = True,
    method="pchip",
    **interpolation,
) -> PandasObj:
    """
    Reindexes `data` and fills new values by interpolation (PCHIP, by default).

    This function was motivated by the fact that :meth:`pandas.DataFrame.resample`
    followed by :meth:`pandas.DataFrame.resample` doesn't take into account
    misaligned datetimes.

    Args:
        data:
            a DataFrame or Series with a datetime index
        new_index:
        preserve_ints:
            after interpolation, columns containing integers in the original
            dataframe are rounded and converted back to int
        method:
            interpolation method (see :meth:`pandas.DataFrame.interpolate`)
        **interpolation:
            other interpolation keyword argument different from `method` passed
            to :meth:`pandas.DataFrame.interpolate`

    Returns:
        a new Dataframe/Series

    See Also:
        :func:`reindex_by_interpolating`
    """
    extended_index = data.index.union(new_index)
    out = data.reindex(extended_index)
    out = out.interpolate(method=method, **interpolation)  # fill NaNs
    out = out.loc[new_index]
    if preserve_ints:
        if isinstance(data, pd.DataFrame):
            int_cols = [
                col for col, dtype in data.dtypes.items() if is_integer_dtype(dtype)
            ]
            out.loc[:, int_cols] = out.loc[:, int_cols].round().astype(int)
        elif is_integer_dtype(data):
            out = out.round().astype(int)

    out.index.rename("date", inplace=True)
    return out


def resample(
    data: PandasObj,
    freq: Union[int, str] = "1D",
    hour: int = 18,
    preserve_ints: bool = True,
    method="pchip",
    **interpolation,
) -> PandasObj:
    """
    Resamples `data` and fills missing values by interpolation.

    The resulting index is a `pandas.DatetimeIndex` whose elements are spaced by
    accordingly to `freq` and having the time set to `{hour}:00`.

    In the case of "day frequencies" ('{num}D'), the index always includes the
    latest date (`data.index[-1]`): the new index is a datetime range built
    going backwards from the latest date.

    This function was motivated by the fact that :meth:`pandas.DataFrame.resample`
    followed by :meth:`pandas.DataFrame.resample` doesn't take into account
    misaligned datetimes. If you want to back-fill or forward-fill, just use
    :meth:`DataFrame.resample`.

    Args:
        data:
            a DataFrame or Series with a datetime index
        freq:
            resampling frequency in `pandas` notation
        hour:
            reference hour; all datetimes in the new index will have this hour
        preserve_ints:
            after interpolation, columns containing integers in the original
            dataframe are rounded and converted back to int
        method:
            interpolation method (see :meth:`pandas.DataFrame.interpolate`)
        **interpolation:
            other interpolation keyword argument different from `method` passed
            to :meth:`pandas.DataFrame.interpolate`

    Returns:
        a new Dataframe/Series with index elements spaced according to ``freq``

    See Also:
        :func:`reindex_by_interpolating`
    """
    if isinstance(freq, int):
        freq = f"{freq}D"
    else:
        freq = freq.upper()

    match = re.fullmatch(r"(\d*)D", freq)
    if match:
        new_index = pd.date_range(
            data.index[-1].replace(hour=hour, minute=0),
            data.index[0].replace(hour=hour, minute=0),
            freq="-1D" if freq == "D" else f"-{freq}",
        )[::-1]
    else:
        new_index = pd.date_range(
            data.index[0],
            data.index[-1].replace(hour=hour, minute=0),
            freq=freq,
        )
    return reindex_by_interpolating(
        data, new_index, preserve_ints=preserve_ints, method=method, **interpolation
    )


# ===========================
#   DATA CORRECTION
# ===========================
def nullify_series_local_bumps(series: pd.Series):
    """ Set to NaN all elements s[i] such that s[i] > s[i+k] """
    curr_min = np.inf
    bad = set()
    for i in reversed(series.index):
        if series[i] > curr_min:
            bad.add(i)
        else:
            curr_min = series[i]
    return series.mask(series.index.isin(bad))


def nullify_local_bumps(df: pd.DataFrame):
    def f(series):
        if "unknown" in series.name:
            return series
        return nullify_series_local_bumps(series)

    return df.apply(f)


def fix_monotonicity(data: pd.DataFrame, method="pchip", **interpolation):
    """
    Replaces tracts of "cases" and "deaths" time series that break the monotonicity
    of the series with interpolated data, ensuring that the sum of male and female
    counts are less or equal to the total count.

    Args:
        data: a DataFrame containing all integer columns about cases and deaths
        method: interpolation method

    Returns:

    """
    # Fix all individual series independently
    orig = only_counts(data)
    fixed = (
        nullify_local_bumps(orig)
        .interpolate(method=method, **interpolation)
        .round()
        .astype(int)
    )

    # Ensure that (males + females <= total) for each age group (including
    # "unknown age" group) taking the maximum between the fixed totals and the
    # fixed males+females
    for variable in ["deaths", "cases"]:
        males_plus_females = fixed[cols("mf", variable)].sum(axis=1, level=1)
        totals = fixed[variable]
        totals_fixed = (
            totals
            .where(totals >= males_plus_females)
            .fillna(males_plus_females)
        )
        fixed[variable] = totals_fixed

    return fixed.astype(int)
