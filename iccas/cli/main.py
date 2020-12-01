import random
import subprocess
from functools import partial
from pathlib import Path
from string import ascii_letters
from textwrap import dedent

import click
import cloup
import matplotlib.pyplot as plt
from click import Choice, FloatRange
from cloup import group, option_group
from matplotlib.animation import FFMpegWriter
from pathvalidate import sanitize_filename
from tqdm import tqdm

import iccas as ic

option = partial(cloup.option, show_default=True)


def to_filename(string: str) -> str:
    return str(sanitize_filename(string, platform='universal')).replace(' ', '_')


def rand_string(length, chars=ascii_letters) -> str:
    return ''.join(random.choice(chars) for _ in range(length))


@group('iccas')
def main():
    plt.style.use('seaborn')


@main.command()
@option_group(
    'Data processing options',
    option('--variable', type=Choice(['cases', 'deaths']), default='cases'),
    option('--window', type=int, default=7,
           help='Size (in days) of the time window'),
    option('-n/-N', '--normalize/--no-normalize', default=True),
    option('--interpolation', type=Choice(['linear', 'pchip']), default='pchip'),
)
@option_group(
    'Figure and chart options',
    option('--population / --no-population', 'show_population', default=True,
           help='if --normalize, do/don\'t plot the age distribution of the '
                'italian population as a reference'),
    option('--figsize', type=(float, float), default=(6.4, 4.8), metavar='WIDTH HEIGHT',
           help='Figure size in inches'),
    option('--lang', type=Choice(['it', 'en']), default='it', help='Language'),
)
@option_group(
    'Video output options',
    option('-s', '--save', default=False, is_flag=True,
           help='Save the video'),
    option('-o', '--overwrite', default=False, is_flag=True,
           help='Overwrite the file if it already exists'),
    option('--out-dir', type=click.Path(file_okay=False), default='.',
           help='Output folder'),
    option('-f', '--filename', 'filename_fmt', default=None,
           help='file name as Python format string taking arguments {window} and {step}'),
    option('--fps', type=int, default=12, help='Frames per second'),
    option('--dpi', type=int, default=200,
           help='Dots per inch. Together with --figsize, determines the resolution'),
    option('--hold-last-frame', type=FloatRange(min=0, max=20), default=2,
           help='Hold the last frame for a specified number of seconds at the '
                'end of the video')
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
    save, overwrite, out_dir, filename_fmt,
    fps, dpi, hold_last_frame,
    figsize, interval, repeat, repeat_delay,
):
    ic.set_locale(lang)
    data = ic.fix_monotonicity(ic.get())[['cases', 'deaths']]

    plt.Figure(figsize=figsize)
    chart = ic.charts.AgeDistributionBarChart(
        data,
        variable=variable,
        normalize=normalize,
        window=window,
        population_distribution=(
            ic.get_population_by_age_group().percentage
            if show_population
            else None
        ),
        resample_kwargs=dict(method=interpolation)
    )
    animation = chart.animation(
        interval=interval,
        repeat=repeat,
        repeat_delay=repeat_delay,  # FIXME: repeat_delay doesn't work, not sure why
    )

    if not save:
        plt.show()
        return 0

    # Create the folder(s) if they don't exist
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True, parents=True)

    # Compute the output path
    if filename_fmt is None:
        title = plt.gca().get_title().lower()
        filename = to_filename(title).capitalize()
    else:
        filename = filename_fmt.format(window=window)
    out_path = (out_dir / filename).with_suffix('.mp4')

    if out_path.exists():
        if overwrite:
            print('Removing file', out_path, '...')
            out_path.unlink()
        else:
            print(f'The file {out_path} already exists. '
                  f'Pass -o/--overwrite to overwrite it.')
            return 1

    # Save the animation to a file with a random name first
    tmp_path = out_dir / (rand_string(16) + out_path.suffix)
    writer = FFMpegWriter(fps=fps, metadata=dict(artist='Me'))
    progress_bar = tqdm(
        desc='Saving the video', total=animation.save_count, unit='frame'
    )
    animation.save(
        str(tmp_path), writer=writer, dpi=dpi,
        progress_callback=lambda *_: progress_bar.update(),
    )
    progress_bar.close()
    print('\n')

    if hold_last_frame:
        print(f'Running FFMpeg to hold the last frame for {hold_last_frame:.1f} seconds:\n')
        pretty_command = dedent(f'''
            ffmpeg -y
               -i {tmp_path}
               -vf tpad=stop_mode=clone:stop_duration={hold_last_frame}
               {out_path}
        ''')
        print(pretty_command, flush=True)
        command_tokens = pretty_command.split()
        result = subprocess.run(command_tokens, capture_output=True)
        tmp_path.unlink()  # remove the temp file
        if result.returncode != 0:
            print('FFMpeg error:\n', result.stderr.decode('utf-8'))
            return 1
    else:
        # Just rename the temp file
        tmp_path.rename(out_path)

    print(f'Video saved to {out_path}')
