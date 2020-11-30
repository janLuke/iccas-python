import pytest

import iccas
from iccas.queries import AGE_GROUPS, FIELDS


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


@pytest.mark.parametrize('cuts, expected_values', [
    (10, AGE_GROUPS),
    (20,  ['0-19', '0-19', '20-39', '20-39', '40-59', '40-59',
           '60-79', '60-79', '>=80', '>=80', 'unknown']),
    (30,  ['0-29', '0-29', '0-29', '30-59', '30-59', '30-59',
           '60-89', '60-89', '60-89', '>=90', 'unknown']),
    ([20, 60],
     ['0-19', '0-19', '20-59', '20-59', '20-59', '20-59',
      '>=60', '>=60', '>=60', '>=60', 'unknown']),
])
def test_age_grouper(cuts, expected_values):
    expected_output = dict(zip(AGE_GROUPS, expected_values))
    assert iccas.age_grouper(cuts) == expected_output
