import datetime
from os.path import dirname, abspath

from .sqlite_import import import_games

TIME_LIMIT_SECONDS = 2

dir = dirname(dirname(abspath(__file__)))


def test_import_cant_be_too_long():
    start = datetime.datetime.now().timestamp()
    import_games(dir + "/logs_ranked/", "/tmp/s2_ranked_test.sql", period_days=60)
    end = datetime.datetime.now().timestamp()

    assert end - start < TIME_LIMIT_SECONDS
