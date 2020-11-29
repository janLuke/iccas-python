from itertools import product
from typing import Dict, Iterable, List, Sequence, Set, Union

import pandas as pd

import iccas as ic
from iccas.charts.common import resample_if_needed
from iccas.types import PandasObj

PREFIX_MAP = {
    "T": "",
    "M": "male_",
    "F": "female_",
}
PREFIX_CODES = set(PREFIX_MAP)
FIELDS = ["cases", "cases_percentage", "deaths", "deaths_percentage", "fatality_rate"]
FIELD_SET = set(FIELDS)

AGE_GROUPS = (
    *(f"{start}-{start + 9}" for start in range(0, 90, 10)),
    ">=90",
    "unknown",
)


def product_join(*string_iterables, sep: str = "") -> Iterable[str]:
    return map(sep.join, product(*string_iterables))


def _check_column_name_part(values: Sequence[str], allowed_values: Set[str], kind: str):
    assert kind in {"prefixes", "fields"}
    if not values:
        raise ValueError(f'empty {kind} not allowed; use "*" to select all prefixes')
    if len(values) != len(set(values)):
        raise ValueError(f"invalid {kind}: duplicates not allowed")
    invalid_values = set(values) - allowed_values
    if invalid_values:
        raise ValueError(f"invalid {kind}: {invalid_values}")


def _check_prefix_codes(prefixes: Sequence[str]):
    _check_column_name_part(prefixes, PREFIX_CODES, "prefixes")


def _check_fields(fields: Sequence[str]):
    _check_column_name_part(fields, FIELD_SET, "fields")


def cols(prefixes: str, fields: Union[str, Sequence[str]] = "*") -> List[str]:
    """
    Generates a list of columns by combining prefixes with fields.

    Args:
        prefixes:
            string containing one or multiple of the following characters:
            - 'm' for males
            - 'f' for females
            - 't' for totals (no prefix)
            - '*' for all

        fields:
            values: 'cases', 'deaths', 'cases_percentage', 'deaths_percentage',
            'fatality_rate', '*'

    Returns:
        a list of string
    """
    field_list: Iterable[str]
    if isinstance(fields, str):
        if fields == "*":
            field_list = list(FIELDS)
        else:
            field_list = fields.split()
            _check_fields(field_list)
    else:
        field_list = fields
        _check_fields(field_list)

    prefix_list: Iterable[str]
    if prefixes == "*":
        prefix_list = PREFIX_MAP.values()
    else:
        prefixes = prefixes.upper()
        _check_prefix_codes(prefixes)
        prefix_list = [PREFIX_MAP[p] for p in prefixes]

    return list(product_join(prefix_list, field_list))


def only_counts(data: pd.DataFrame) -> pd.DataFrame:
    """Returns only cases and deaths columns (including sex-specific columns),
    dropping all other columns that are computable from these."""
    return data[
        [
            "cases",
            "female_cases",
            "male_cases",
            "deaths",
            "female_deaths",
            "male_deaths",
        ]
    ]


def only_cases(data: pd.DataFrame) -> pd.DataFrame:
    """ Returns only columns ['cases', 'female_cases', 'male_cases'] """
    return data[["cases", "female_cases", "male_cases"]]


def only_deaths(data: pd.DataFrame) -> pd.DataFrame:
    """ Returns only columns ['deaths', 'female_deaths', 'male_deaths'] """
    return data[["deaths", "female_deaths", "male_deaths"]]


def age_grouper(
    cuts: Union[int, Sequence[int]],
    fmt_last: str = ">={}",
) -> Dict[str, str]:
    if isinstance(cuts, int):
        if cuts % 10 != 0 or cuts < 0:
            raise ValueError()
        cuts = list(range(0, 100, cuts))
    else:
        for c in cuts:
            if c < 0 or c % 10 != 0:
                raise ValueError(f"at least one cut is not multiple of 10: {c}")
        if any(cuts[i - 1] >= cuts[i] for i in range(1, len(cuts))):
            raise ValueError(f"cuts  are not in increasing order: {cuts}")

    keys = AGE_GROUPS
    starts = [0, *cuts[:-1]]
    widths = [(end - start) // 10 for start, end in zip(starts, cuts)]
    grouper = {}

    k = 0
    for start, cut, width in zip(starts, cuts, widths):
        end = cut - 1
        value = f"{start}-{end}"
        for _ in range(width):
            grouper[keys[k]] = value
            k += 1
    last_value = fmt_last.format(cuts[-1])
    for _ in range(10 - len(grouper)):
        grouper[keys[k]] = last_value
        k += 1
    grouper["unknown"] = "unknown"
    return grouper


def aggregate_age_groups(
    counts: PandasObj,
    cuts: Union[int, Sequence[int]],
    fmt_last: str = ">={}",
) -> PandasObj:
    """
    Aggregates counts for different age groups summing them together.

    Args:
        counts:
            can be a Series with age groups as index or a DataFrame with
            age groups as columns, either in a simple Index or in
            a MultiIndex (no matter in what level)
        cuts:
            a single integer N means "cuts each N years";
            a sequence of integers determines the start ages of new age groups.
        fmt_last:
            format string for the last "unbounded" age group

    Returns:
        A Series/DataFrame with the same "structure" of the input but with
        aggregated age groups.
    """
    grouper = age_grouper(cuts=cuts, fmt_last=fmt_last)
    if isinstance(counts, pd.Series):
        return counts.groupby(grouper).sum()
    d = counts
    if "age_group" in counts.columns.names:
        d = counts.stack("age_group")
    d = d.reset_index("age_group")

    result = (
        d.assign(age_group=d.age_group.apply(grouper.__getitem__))
            .groupby(["date", "age_group"])
            .sum()
            .unstack("age_group")
    )

    if not isinstance(counts.columns, pd.MultiIndex):
        return result.droplevel(axis=1, level=0)
    return result


def get_unknown_sex_count(counts: pd.DataFrame, variable: str) -> pd.DataFrame:
    """ Returns cases/deaths of unknown sex for each age group """
    if variable not in {"cases", "deaths"}:
        raise ValueError("variable should be 'cases' or 'deaths'")
    total = counts[variable]
    sum_of_sexes = counts[f"male_{variable}"] + counts[f"female_{variable}"]
    return total - sum_of_sexes


def running_count(
    counts: PandasObj,
    window: int = 7,
    step: int = 1,
    **resample_kwargs
) -> PandasObj:
    """
    Given counts for cases and/or deaths, returns the number of new cases inside
    a temporal window of ``window`` days that moves forward by steps of ``step`` days.

    Args:
        counts:
        window:
        step:

    Returns:
    """
    if window % step != 0:
        raise ValueError("'window' must be a multiple of 'step'")
    r = ic.resample(counts, freq=step, **resample_kwargs)
    diff_periods = window // step
    out = r.diff(diff_periods).iloc[diff_periods:].round().astype(int)
    out.index = out.index.to_period(f'{window}D')
    return out


def running_average(
    counts: PandasObj,
    window: int = 7,
    step: int = 1,
    **resample_kwargs
) -> PandasObj:
    """
    Given counts for cases/deaths, returns the average daily number of
    new cases/deaths inside a temporal window of ``window``, moving the window
    ``step`` days a time.

    Args:
        counts:
        window:
        step:

    Returns:
    """
    return running_count(counts, window, step, **resample_kwargs) / window


def count_by_period(counts: PandasObj, freq: Union[str, int]) -> PandasObj:
    if isinstance(freq, int):
        freq = f'{freq}D'
    r = ic.resample(counts, freq=freq)
    r = r.diff().dropna()
    r.index = r.index.to_period(freq=freq).rename('period')
    return r


def average_by_period(counts: PandasObj, freq: Union[str, int]) -> PandasObj:
    c = count_by_period(counts, freq)
    lengths = (c.index.end_time - c.index.start_time + pd.Timedelta(nanoseconds=1)).days
    return c.div(lengths, axis=0)


def fatality_rate(counts, shift):
    """
    Computes the fatality rate as a ratio between the total number of deaths and
    the total number of cases ``shift`` days before.

    ``counts`` is resampled with interpolation if needed.
    """
    resampled = resample_if_needed(counts, freq='1D')
    shifted_cases = resampled.cases.shift(shift).iloc[shift:]
    deaths = resampled.deaths.iloc[shift:]
    cfr = (deaths / shifted_cases)
    if 'unknown' in cfr.columns:
        cfr = cfr.drop(columns='unknown')
    return cfr
