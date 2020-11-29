import pytest

import iccas
from iccas.queries import FIELDS


# fmt: off
@pytest.mark.parametrize("prefixes, fields, expected", [
    ("m", "cases deaths", ["male_cases", "male_deaths"]),
    ("f", "cases deaths", ["female_cases", "female_deaths"]),
    ("t", "*", FIELDS),
    (
        "mf",
        "cases deaths",
        ["male_cases", "male_deaths", "female_cases", "female_deaths"],
    ),
    ("*", "cases", ["cases", "male_cases", "female_cases"]),
])
# fmt: on
def test_cols(prefixes, fields, expected):
    print("ciao")
    actual = iccas.cols(prefixes, fields)
    assert actual == expected


def test_cols_raises_for_invalid_prefix():
    with pytest.raises(ValueError, match="prefixes"):
        iccas.cols("g")
    with pytest.raises(ValueError, match="duplicates"):
        iccas.cols("mfm")
    with pytest.raises(ValueError, match="empty"):
        iccas.cols("")


def test_cols_raises_for_invalid_fields():
    with pytest.raises(ValueError):
        iccas.cols("*", "counts")
    with pytest.raises(ValueError):
        iccas.cols("*", "cases, deaths")
    with pytest.raises(ValueError, match="empty"):
        iccas.cols("*", "")
