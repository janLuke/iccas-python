__author__ = """Gianluca Gippetto"""
__email__ = "gianluca.gippetto@gmail.com"
__version__ = "0.1.0"

__all__ = (
    "charts",
    "checks",
    "cols",
    "get",
    "get_by_date",
    "get_url",
    "load",
    "load_single_date",
    "only_cases",
    "only_counts",
    "only_deaths",
    "resample",
    "reindex_by_interpolating",
    "fix_monotonicity",
    "age_grouper",
    "aggregate_age_groups",
    "get_unknown_sex_count",
    "get_population_by_age",
    "get_population_by_age_group",
    "running_average",
    "running_count",
    "fatality_rate",
)

from .i18n import language, set_language, set_locale

from .loading import (
    load_single_date,
    load,
    get,
    get_by_date,
    get_url,
    get_population_by_age,
    get_population_by_age_group,
)
from .processing import (
    reindex_by_interpolating,
    resample,
    fix_monotonicity,
)
from .queries import (
    age_grouper,
    cols,
    aggregate_age_groups,
    only_cases,
    only_counts,
    only_deaths,
    get_unknown_sex_count,
    running_count,
    running_average,
    count_by_period,
    average_by_period,
    fatality_rate,
)
from . import checks
from . import charts
from . import queries
