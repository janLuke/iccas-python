from typing import Optional

import matplotlib as mpl
import pandas as pd
from matplotlib import pyplot as plt

import iccas as ic
import iccas.i18n
from iccas.i18n import translated
from iccas.i18n.lib import Translation
from iccas.charts.common import (
    DEFAULT_CMAP,
    Period,
    check_age_group_size,
    check_variable,
    legend,
    resample_if_needed,
)

DOUBLE_CHART_FIGSIZE = (15, 15)


@translated()
def area_chart(
    counts_over_time: pd.DataFrame,
    *,
    strings: Translation,
    normalize: bool = False,
    ax: Optional[plt.Axes] = None,
    cmap=DEFAULT_CMAP,
    alpha: float = 0.8,
    **kwargs,
) -> plt.Axes:
    """
    A base for stacked area charts (tuned for iccas charts).

    Args:
        counts_over_time:
            a DataFrame with a DateTimeIndex and a column for each age group
            (e.g. ``ic.get().cases``)
        strings:
        normalize:
        ax:
        cmap:
        alpha:
        **kwargs:

    Returns:

    """
    data = counts_over_time
    if normalize:
        data = data.divide(data.sum(axis=1), axis=0)
    ax = data.plot.area(ax=ax, alpha=alpha, cmap=cmap, **kwargs)
    if normalize:
        ax.set_ylim([0, 1.0])
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1.0, decimals=0))
    else:
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter("{x:n}"))
    ax.set_xlabel("")
    ax.set_xlim(data.index[0], data.index[-1])
    legend(ax, title=strings["age"])
    return ax


@translated("""
    en:
        title.cases: Coronavirus cases in Italy since the beginning of the pandemic
        title.deaths: Deaths for coronavirus in Italy since the beginning of the pandemic
    it:
        title.cases: Casi di coronavirus dall'inizio della epidemia
        title.deaths: Decessi per coronavirus dall'inizio della pandemia
""")
def double_area_chart_of_cumulative_counts(
    data: pd.DataFrame,
    variable: str = "cases",
    *,
    age_group_size: int = 20,
    period: Optional[Period] = None,
    strings: Translation,
    **figure_args,
) -> plt.Figure:
    """
    Not a very interesting chart.

    Args:
        data:
            DataFrame having 'cases' and/or 'deaths' as first-level columns
            (e.g. ``ic.get()``)
        variable:
        age_group_size:
        period:
        strings:
        lang:

    Returns:

    """
    check_variable(variable)
    check_age_group_size(age_group_size)
    period = slice(*period) if period else slice(data.index[0], None)

    # resample for a smoother graph
    d = resample_if_needed(data[variable], "D", hour=18, method="pchip")
    d = ic.aggregate_age_groups(
        d[period].drop(columns="unknown"),
        cuts=age_group_size,
        fmt_last="{}+",
    )

    figure_args.setdefault("figsize", DOUBLE_CHART_FIGSIZE)
    fig, ax = plt.subplots(2, 1, **figure_args)
    title = strings[f"title.{variable}"]
    ax[0].set_title(title)
    area_chart(d, ax=ax[0], lang=strings.lang)
    area_chart(d, normalize=True, ax=ax[1], lang=strings.lang)


@translated()
def double_area_chart_of_running_averages(
    data: pd.DataFrame,
    variable: str = "cases",
    *,
    strings: Translation,
    window: int = 14,
    age_group_size: int = 20,
    period: Optional[Period] = None,
    **figure_args,
):
    check_variable(variable)
    check_age_group_size(age_group_size)
    period = slice(*period) if period else slice(data.index[0], None)

    r = resample_if_needed(data[variable].drop(columns="unknown"), "D")
    d = r[period]
    d = d.diff(window).iloc[window:]
    d = ic.aggregate_age_groups(d, cuts=age_group_size, fmt_last="{}+")
    if window > 1:
        d = d / window

    figure_args.setdefault("figsize", DOUBLE_CHART_FIGSIZE)
    fig, ax = plt.subplots(2, 1, **figure_args)
    area_chart(d, ax=ax[0], lang=strings.lang)
    area_chart(d, ax=ax[1], normalize=True, lang=strings.lang)
    ax[0].set_title(strings.get(f"running_average_{variable}_title", count=window))
    return fig


if __name__ == "__main__":
    plt.style.use('seaborn')
    resampled = ic.resample(ic.get()[["cases"]])

    iccas.i18n.set_language('en')
    double_area_chart_of_running_averages(resampled, window=14)
    plt.show()

    iccas.i18n.set_language('it')
    double_area_chart_of_running_averages(resampled, window=14)
    plt.show()
