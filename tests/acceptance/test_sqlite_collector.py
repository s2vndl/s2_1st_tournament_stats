import datetime
import sqlite3

import pandas as pd

from s2_analytics.collect.sqlite_collector import SqliteCollector
from s2_analytics.collect.summary_collector import SummaryCollector, Summary
from tests.game_builder import GameBuilderFactory
from s2_analytics.tools import process_games


class TestSummarizingDatasets:
    def setup_method(self):
        self.conn = sqlite3.connect("file::memory:")
        self.sqlite_collector = SqliteCollector(sqlite_conn=self.conn).init()
        self.collectors = [self.sqlite_collector]

    def test_generates_overview_of_data_set(self):
        teams = {"Red": ["A"], "Blue": ["B"]}
        start_time_1 = 1675452534000
        start_time_2 = 1675733734000
        games = GameBuilderFactory(teams=teams) \
            .add_game(game_start_time=start_time_1, playlist="CTF-Standard-4") \
            .add_round(map="ctf_x") \
            .add_cap(player="A") \
            .build() \
            .add_game(game_start_time=start_time_2, playlist="CTF-Standard-6") \
            .add_round(map="ctf_X") \
            .add_cap(player="A") \
            .build() \
            .finish()

        process_games(games, self.collectors)

        cur = self.conn.cursor()

        fetchall = cur.execute("select distinct mapName from round").fetchall()
        assert fetchall == [("ctf_x",)]

