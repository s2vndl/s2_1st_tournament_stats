from io import StringIO

import pandas as pd


def assert_dataframes_equal(expected, actual):
    expected = "\n".join([x.strip() for x in expected.split("\n")])
    expected_dataframe = pd.read_csv(StringIO(expected), parse_dates=["date"])
    assert expected_dataframe.to_dict() == actual.to_dict()
