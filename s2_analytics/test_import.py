import datetime
from os.path import dirname, abspath

from .importer import import_games, GameData, RoundData, EventKill, EventFlagCap
from s2_analytics.collector.object_collector import ObjectCollector

TEST_DB = "/tmp/s2_ranked_test.sql"
SCRIPT_DIR = dirname(dirname(abspath(__file__)))
TIME_LIMIT_SECONDS = 2


def test_import_cant_be_too_long():
    start = datetime.datetime.now().timestamp()
    collector = ObjectCollector()
    import_games(SCRIPT_DIR + "/logs_ranked/", period_days=5, processors=[collector])
    end = datetime.datetime.now().timestamp()

    assert len(collector.games) > 0
    assert end - start < TIME_LIMIT_SECONDS


def test_reading_games():
    collector = ObjectCollector()
    import_games(SCRIPT_DIR + "/fixtures/", period_days=99999, processors=[collector])

    assert len(collector.games) == 1

    game = GameData(1673564249000, datetime.datetime(2023, 1, 12, 22, 57, 29), "CTF-Standard-6", 0, 2)
    rnd = [
        RoundData(game.id, 0, 'ctf_x', datetime.datetime(2023, 1, 12, 22, 58, 16, 797000), 1673564296797,
                  datetime.datetime(2023, 1, 12, 23, 2, 32, 13000), 0, 1),
        RoundData(game.id, 1, 'ctf_ash', datetime.datetime(2023, 1, 12, 22, 58, 18, 797000), 1673564298797,
                  datetime.datetime(2023, 1, 12, 23, 2, 34, 13000), 0, 1),
    ]

    events = [
        EventKill(game.id, rnd[0].number, datetime.datetime(2023, 1, 12, 22, 58, 30, 905000), 'C19637F2290726EB',
                  'Blue',
                  '85D4CB1D1C2A72CD', 'Red', 'Barrett'),
        EventFlagCap(game.id, rnd[0].number, datetime.datetime(2023, 1, 12, 23, 2, 7, 881000), 231084,
                     '924A515947815DE1',
                     'Blue')
    ]

    assert [game] == collector.games
    assert rnd == collector.rounds
    assert events == collector.events[:2]
