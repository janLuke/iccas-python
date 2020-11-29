from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import iccas as ic
from iccas.charts.common import DEFAULT_CMAP, legend
from iccas.i18n import translated
from iccas.i18n.lib import Translation


def add_labels_to_bars(
    rects: List[plt.Rectangle],
    fmt: str = '{:.1f}',
    ax: Optional[plt.Axes] = None,
    y_offset: int = 7,   # in points
    **kwargs,
) -> Tuple[List[plt.Annotation], Callable[[], None]]:
    """
    Attach a text label above each bar in ``rects``, displaying its height.
    Returns a tuple with the list of labels and a function to update the labels
    (useful for animations)
    """
    ax = ax or plt.gca()
    labels = []
    for rect in rects:
        height = rect.get_height()
        label = ax.annotate(
            fmt.format(height),
            xy=(rect.get_x() + rect.get_width() / 2, height),
            ha='center', va='bottom',
            xytext=(0, y_offset), textcoords="offset points",
            **kwargs,
        )
        labels.append(label)

    def update_labels():
        for label, rect, in zip(labels, rects):
            height = rect.get_height()
            label.set_text(fmt.format(height))
            label.xy = label.xy[0], height
            label.xyann = (0, y_offset)

    return labels, update_labels


@translated()
class AgeDistributionBarChart:
    def __init__(
        self,
        counts: pd.DataFrame,
        variable: str = "cases",
        *,
        strings: Translation,
        normalize: bool = True,
        age_group_size: int = 10,
        window: int = 14,
        population_distribution: pd.Series = None,
        ax: plt.Axes = None,
        resample_kwargs: Dict[str, Any] = {},
    ):
        """
        Shows the age distribution of cases/deaths at a given date.
        Usable either to draw a static chart or to generate an animation.

        Args:
            counts:
            variable:
            normalize:
            age_group_size:
            window:
            population_distribution:
            ax:
            lang:
        """
        self.ax = ax = ax or plt.gca()
        s = strings
        data = (
            counts[variable]
            .drop(columns="unknown")
            .pipe(ic.running_average, **resample_kwargs)
            .pipe(ic.aggregate_age_groups, cuts=age_group_size)
        )
        if normalize:
            data = data.divide(data.sum(axis=1), axis=0)
            ax.yaxis.set_major_formatter(
                mpl.ticker.PercentFormatter(xmax=1.0, decimals=0)
            )
        self.data = data

        if normalize and population_distribution is not None:
            population = ic.aggregate_age_groups(
                population_distribution, cuts=age_group_size
            )
            sns.set_color_codes("pastel")
            sns.barplot(
                ax=ax,
                label=s["istat_population_data_label"],
                x=population.index,
                y=population,
                facecolor='b',
                hatch="/",
                edgecolor="white",
            )

        sns.set_color_codes("muted")
        age_groups = data.columns
        label = s[f"{variable}_label"]
        self.bars = ax.bar(
            x=age_groups,
            height=[0] * len(age_groups),
            label=label,
            facecolor='b',
            alpha=0.7,
        )
        self.labels, self.update_labels = add_labels_to_bars(
            self.bars,
            fmt='{:.0%}' if normalize else '{:n}',
            fontsize=10,
            ax=ax,
            color='white',
            bbox=dict(
                boxstyle=mpl.patches.BoxStyle("Round", pad=0.3),
                color='black', alpha=.35,
            ),
        )
        ymax = 1.05 * data.max().max()
        ax.set_ylim(0, ymax)
        ax.set_xticklabels(age_groups)
        ax.set_xlabel(s["age"])
        ax.set_ylabel("")
        ax.grid(False, which='both', axis='x')
        if normalize:
            title = s.get(f"running_{variable}_age_distribution", count=window)
        else:
            title = s.get(f"running_average_{variable}_title", count=window)
        ax.set_title(title, fontsize=14)
        if normalize and population_distribution is not None:
            ax.yaxis.set_major_formatter(
                mpl.ticker.PercentFormatter(xmax=1.0, decimals=0)
            )
            ax.legend()

        self.date_text = ax.text(
            0.5,
            0.93,
            "",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color=(1, 1, 1, 0.9),
            bbox=dict(
                boxstyle=mpl.patches.BoxStyle("Round", pad=0.4),
                color=(0.5, 0.5, 0.5, 0.5),
            ),
            fontsize=14,
            fontweight="semibold",
        )
        self.artists = [
            self.date_text,
            *self.bars,
            *self.labels
        ]

    def show(self, date: pd.Timestamp):
        d = self.data.loc[date]
        if isinstance(d, pd.DataFrame):
            if len(d) > 1:
                raise ValueError(f'"{date}" matches more than one date')
            d = d.stack("age_group")
        for bar, h in zip(self.bars, d):
            bar.set_height(h)
        formatted_date = date.strftime("%d %B %Y")
        self.date_text.set_text(formatted_date)
        self.update_labels()
        return self.artists

    def animation(self, **kwargs) -> mpl.animation.FuncAnimation:
        kwargs = {"blit": True, "repeat": False, "interval": 50, **kwargs}
        return mpl.animation.FuncAnimation(
            self.ax.figure, self.show, frames=self.data.index, **kwargs
        )


def age_dist_bar_chart(
    counts: pd.DataFrame,
    date: pd.Timestamp,
    variable: str = "cases",
    *,
    normalize: bool = True,
    age_group_size: int = 10,
    window: int = 14,
    population_distribution: pd.Series = None,
    ax: plt.Axes = None,
    lang: Optional[str] = None,
):
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 7))
    AgeDistributionBarChart(
        ax=ax,
        counts=counts,
        variable=variable,
        normalize=normalize,
        age_group_size=age_group_size,
        window=window,
        population_distribution=population_distribution,
        lang=lang,
    ).show(date)


@translated()
def average_by_period_bar_chart(
    counts: pd.DataFrame,
    variable: str,
    *,
    strings: Translation,
    freq: Union[str, int] = 7,
    normalize: bool = False,
    age_group_size: int = 20,
    stacked: bool = True,
    ylim: float = None,
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[float, float] = (12, 7),
) -> plt.Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    # Data preparation
    d = counts[variable].drop(columns='unknown')
    d = ic.aggregate_age_groups(d, age_group_size)
    d = ic.count_by_period(d, freq=freq)
    if normalize:
        d = d.div(d.sum(axis=1), axis=0)

    # Plot
    ax = d.plot.bar(stacked=stacked, cmap=DEFAULT_CMAP, ax=ax, width=.85)
    legend(ax=ax, title=strings['age'])

    # Axes setup
    if freq == 'M':
        xlabel = strings['month']
        date_fmt = '%B'
        xtick_rotation = 0
    else:
        xlabel = strings['period_end_date']
        date_fmt = '%d %b'
        xtick_rotation = 45
    ax.set_xticklabels(d.index.strftime(date_fmt), rotation=xtick_rotation)
    ax.set_xlabel(xlabel)
    if normalize:
        if stacked:
            ax.set_ylim([0, 1.0])
        ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1.0, decimals=0))
    else:
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:n}'))
        if ylim:
            ax.set_ylim(0, ylim * ax.get_ylim()[1])

    # Title
    base_title = strings[
        f'{variable}_age_distribution' if normalize else f'average_daily_{variable}'
    ]
    if freq == 'M':
        period_label = strings['month_by_month']
    elif freq == 7 or (isinstance(freq, str) and freq.startswith('W')):
        period_label = strings['week_by_week']
    elif isinstance(freq, int):
        period_label = strings.get('by_periods_of_n_days', count=freq)
    title = f"{base_title} {period_label}"
    ax.set_title(title)

    return ax


if __name__ == '__main__':
    plt.style.use('seaborn')
    ic.set_locale('it')
    df = ic.fix_monotonicity(ic.get())
    anim = AgeDistributionBarChart(
        df, population_distribution=ic.get_population_by_age_group().percentage
    ).animation()
    plt.show()
