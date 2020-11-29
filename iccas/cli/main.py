from pathlib import Path

import click
import matplotlib.pyplot as plt
from cloup import group, option, option_group
from matplotlib.animation import FFMpegWriter
from pathvalidate import sanitize_filename
from tqdm import tqdm

import iccas as ic


def to_filename(string: str) -> str:
    return sanitize_filename(string, platform='universal').replace(' ', '_')


@group('iccas')
def main():
    plt.style.use('seaborn')


@main.command()
@option_group(
    'Chart options',
    option('--variable', type=click.Choice(['cases', 'deaths']), default='cases'),
    option('--window', type=int, default=7,
           help='Size (in days) of the time window'),
    option('-n/-N', '--normalize/--no-normalize', default=True),
    option('--interpolation', type=click.Choice(['linear', 'pchip']), default='pchip'),
    option('--population / --no-population', 'show_population', default=True,
           help='if --normalize, show the distribution of the italian population '
                'age distribution as a reference'),
    option('--lang', type=click.Choice(['it', 'en']), default='it'),
)
@option_group(
    'Video output options',
    option('-s', '--save', default=False, is_flag=True),
    option('--out-dir', type=click.Path(file_okay=False), default='.'),
    option('-f', '--filename', 'filename_fmt', default=None,
           help='file name as Python format string taking arguments {window} and {step}'),
    option('--fps', type=int, default=15),
    option('--dpi', type=int, default=200),
)
@option_group(
    'Interactive plot options',
    option('--interval', default=50),
    option('--repeat', type=bool, default=False),
    option('--repeat-delay', default=2000),
)
def age_dist_animation(
    variable, show_population, lang,
    window, normalize, interpolation,
    save, out_dir, filename_fmt, fps, dpi,
    interval, repeat, repeat_delay,
):
    ic.set_locale(lang)
    data = (
        ic.get()
        .pipe(ic.fix_monotonicity)
        [['cases', 'deaths']]
    )

    animation = ic.charts.AgeDistributionBarChart(
        data,
        variable=variable,
        normalize=normalize,
        window=window,
        population_distribution=(
            ic.get_population_by_age_group().percentage
            if show_population
            else None
        ),
        resample_kwargs=dict(
            method=interpolation,
        )
    ).animation(
        interval=interval,
        repeat=repeat,
        repeat_delay=repeat_delay,
    )

    if save:
        out_dir = Path(out_dir)
        out_dir.mkdir(exist_ok=True, parents=True)
        if filename_fmt is None:
            title = plt.gca().get_title().lower()
            filename = to_filename(title)
        else:
            filename = filename_fmt.format(window=window)
        out_path = (out_dir / filename).with_suffix('.mp4')
        print(out_path)
        writer = FFMpegWriter(fps=fps, metadata=dict(artist='Me'))
        progress_bar = tqdm(
            desc='Saving the video', total=animation.save_count, unit='frame'
        )
        animation.save(
            str(out_path), writer=writer, dpi=dpi,
            progress_callback=lambda *_: progress_bar.update(),
        )
        print(out_path)
    else:
        plt.show()
