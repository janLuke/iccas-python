"""
Sanity checks.
"""


def is_non_decreasing(df):
    deltas = df.drop(columns="unknown", level=1).diff(1).dropna()
    return (deltas >= 0).all(axis=None)


def totals_not_less_than_sum_of_sexes(data, variable):
    assert variable in {"cases", "deaths"}
    total = data[variable]
    sum_of_sexes = data[f"male_{variable}"] + data[f"female_{variable}"]
    return (total - sum_of_sexes >= 0).all(axis=None)
