import datetime
import sqlite3

from s2_analytics.collect.sqlite_collector import SqliteCollector
from s2_analytics.collect.summary_collector import SummaryCollector, Summary
from tests.game_builder import GameBuilderFactory
from s2_analytics.tools import process_games


class TestSummarizingDatasets:
    def setup_method(self):
        conn = sqlite3.connect("file::memory:")
        sqlite_collector = SqliteCollector(sqlite_conn=conn).init()
        self.summary_collector = SummaryCollector(conn, sqlite_collector)
        self.collectors = [sqlite_collector, self.summary_collector]

    def test_generates_overview_of_data_set(self):
        teams = {"Red": ["A"], "Blue": ["B"]}
        start_time_1 = 1675452534000
        start_time_2 = 1675733734000
        games = GameBuilderFactory(teams=teams) \
            .add_game(game_start_time=start_time_1, playlist="CTF-Standard-4") \
            .add_round(map="ctf_x") \
            .add_cap(player="A") \
            .add_round(map="ctf_ash") \
            .add_cap(player="A") \
            .build() \
            .add_game(game_start_time=start_time_2, playlist="CTF-Standard-6") \
            .add_round(map="ctf_x") \
            .add_cap(player="A") \
            .build() \
            .finish()

        process_games(games, self.collectors)

        assert self.summary_collector.get_summary() == Summary(datetime.datetime.fromisoformat("2023-02-03T19:28:54"),
                                                               datetime.datetime.fromisoformat("2023-02-07T01:35:34"), 2, 3,
                                                               {"CTF-Standard-4": 1, "CTF-Standard-6": 1})

        assert self.summary_collector.get_summary().to_table() == [
            ["First game", "2023-02-03"],
            ["Last game", "2023-02-07"],
            ["Games total", 2],
            ["Rounds total", 3],
            ["Games in playlist `CTF-Standard-4`", 1],
            ["Games in playlist `CTF-Standard-6`", 1],
        ]
