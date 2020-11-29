import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
from iccas.caching import RemoteFolderProxy
from iccas.types import DateLike, PathType

BASE_URL = (
    "https://raw.githubusercontent.com/janLuke/iccas-dataset/master/data/"
)
AVAILABLE_FORMATS = {"csv"}
DEFAULT_CACHE_DIR = Path("~/.iccas").expanduser()
POPULATION_BY_AGE_PATH = "util/italian_population_by_age_2020.csv"
POPULATION_BY_AGE_GROUP_PATH = "util/italian_population_by_age_group_2020.csv"


def _check_file_format(fmt: str):
    if fmt not in AVAILABLE_FORMATS:
        raise ValueError(f"unavailable format: {fmt}")


def _date_as_str(date: DateLike) -> str:
    if isinstance(date, str):
        return date
    if isinstance(date, datetime.date):
        return date.strftime("%Y-%m-%d")
    raise TypeError


def _get_dataset_path(date: Optional[DateLike] = None, fmt: str = "csv") -> str:
    if date:
        date_str = _date_as_str(date)
        return "by-date/iccas_{}.{}".format(date_str, fmt)
    return "iccas_full.{}".format(fmt)


def get_url(date: Optional[DateLike] = None, fmt: str = "csv") -> str:
    """Returns the url of a dataset in a given format. If `date` is None,
    returns the URL of the full dataset."""
    _check_file_format(fmt)
    return urljoin(BASE_URL, _get_dataset_path(date=date, fmt=fmt))


def load(path: PathType) -> pd.DataFrame:
    dataset = pd.read_csv(path, index_col=("date", "age_group"), parse_dates=["date"])
    return dataset.unstack(level="age_group")


def load_single_date(path: PathType, keep_date: bool = False) -> pd.DataFrame:
    """
    Loads a dataset containing data for a single date.

    By default (`keep_date=False`), the `date` column is dropped and the
    datetime is stored in the `attrs` of the DataFrame.
    If instead `keep_date=True`, the returned dataset has a MultiIndex
    `(date, age_group)`.

    Args:
        path:
        keep_date: whether to drop the date column (containing a single datetime value)
    """
    index_col = ("date", "age_group") if keep_date else "age_group"
    dataset = pd.read_csv(path, index_col=index_col, parse_dates=["date"])
    if not keep_date:
        date = dataset.date.iloc[0]
        dataset = dataset.drop(columns="date")
        dataset.attrs["date"] = date
    return dataset


def get(cache_dir: PathType = DEFAULT_CACHE_DIR) -> pd.DataFrame:
    """
    Returns the latest version of the ICCAS dataset in a
    :class:`pandas.DataFrame` (as it's returned by :func:`load`).

    This function uses :meth:`RemoteFolderCache.get`, which caches.

    Raises:
        :exc:`request.exceptions.ConnectionError`: if the server is unreachable
        and no dataset is available in `cache_dir`
    """
    data_proxy = RemoteFolderProxy(folder_url=BASE_URL, local_path=cache_dir)
    path = data_proxy.get(_get_dataset_path())
    return load(path)


def get_by_date(
    date: DateLike,
    keep_date: bool = False,
    cache_dir: PathType = DEFAULT_CACHE_DIR,
) -> Tuple[pd.DataFrame, pd.Timestamp]:
    data_proxy = RemoteFolderProxy(folder_url=BASE_URL, local_path=cache_dir)
    path = data_proxy.get(_get_dataset_path(date=date))
    return load_single_date(path, keep_date=keep_date)


def get_population_by_age(cache_dir: PathType = DEFAULT_CACHE_DIR) -> pd.DataFrame:
    """
    Returns a DataFrame with "age" as index and two columns:
    "value" (absolute counts) and "percentage" (<=1.0)
    """
    data_proxy = RemoteFolderProxy(folder_url=BASE_URL, local_path=cache_dir)
    path = data_proxy.get(POPULATION_BY_AGE_PATH)
    pop = pd.read_csv(path, index_col=0)
    pop['percentage'] = pop.value / pop.value.sum()
    return pop


def get_population_by_age_group(
    cache_dir: PathType = DEFAULT_CACHE_DIR,
) -> pd.DataFrame:
    """
    Returns a DataFrame with "age_group" as index and two columns:
    "value" (absolute counts) and "percentage" (<=1.0)
    """
    data_proxy = RemoteFolderProxy(folder_url=BASE_URL, local_path=cache_dir)
    path = data_proxy.get(POPULATION_BY_AGE_GROUP_PATH)
    pop = pd.read_csv(path, index_col=0)
    pop['percentage'] = pop.value / pop.value.sum()
    return pop
