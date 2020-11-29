import datetime
from pathlib import Path
from typing import TypeVar, Union

import pandas as pd

DateLike = Union[str, datetime.date]
PathType = Union[str, Path]
PandasObj = TypeVar("PandasObj", pd.Series, pd.DataFrame)
