import datetime
from os.path import dirname, abspath

from .constants import FILTER_PLAYLIST_CTF
from .game_builder import GameBuilderFactory, GameBuilder
from .importer import import_games, GameDetails, RoundData, EventKill, EventFlagCap
from s2_analytics.collector.object_collector import GameObjectCollector
from .tools import process_games

TEST_DB = "/tmp/s2_ranked_test.sql"
SCRIPT_DIR = dirname(dirname(abspath(__file__)))
TIME_LIMIT_SECONDS = 2


def test_import_cant_be_too_long():
    start = datetime.datetime.now().timestamp()
    collector = GameObjectCollector()
    import_games(SCRIPT_DIR + "/logs_ranked/", period_days=30, processors=[collector], game_filters=[FILTER_PLAYLIST_CTF])
    end = datetime.datetime.now().timestamp()

    assert len(collector.games) > 100
    assert end - start < TIME_LIMIT_SECONDS


def test_filtering_games_by_properties():
    games = GameBuilderFactory(teams={"Red": ["A"], "Blue": ["B"]}) \
        .add_game(match_quality=0.9, game_start_time=123) \
        .add_round() \
        .add_cap(player="A") \
        .build() \
        .add_game(match_quality=0.8, game_start_time=124) \
        .add_round() \
        .add_cap(player="A") \
        .build() \
        .finish()

    collector = GameObjectCollector()
    process_games(games, [collector])
    assert len(collector.games) == 2

    collector = GameObjectCollector()
    process_games(games, [collector], [lambda g: g.match_quality > 0.85])
    assert len(collector.games) == 1
    assert collector.games[0].details.match_quality == 0.9
