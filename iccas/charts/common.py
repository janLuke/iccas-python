from typing import Optional, Tuple, Union

import pandas as pd
import matplotlib.pyplot as plt

import iccas as ic

VARIABLES = {"cases", "deaths"}
DEFAULT_CMAP = "inferno"

PeriodBoundary = Union[str, pd.Timestamp]
Period = Tuple[PeriodBoundary, PeriodBoundary]


def check_variable(variable: str):
    if variable not in {"cases", "deaths"}:
        raise ValueError(f"invalid variable: '{variable}' is not in {VARIABLES}")


def check_age_group_size(size: int):
    if size % 10 != 0 or size <= 0:
        raise ValueError(f"invalid age_group_size: {size}")


def legend(ax: Optional[plt.Axes] = None, **kwargs):
    """ Legend positioned at the right of the axes. """
    ax = ax or plt.gca()
    return ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), **kwargs)


def resample_if_needed(data: pd.DataFrame, freq: str = '1D', **kwargs):
    if data.index.freq is None or data.index.freq.freqstr != freq:
        return ic.resample(data, freq, **kwargs)
    return data
