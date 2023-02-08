import datetime
import sqlite3
from collections import OrderedDict
from dataclasses import dataclass

from s2_analytics.collect.sqlite_collector import SqliteCollector
from s2_analytics.game_builder import GameBuilderFactory
from s2_analytics.tools import process_games


@dataclass
class Summary:
    first_game_starttime: datetime.datetime
    last_game_starttime: datetime.datetime
    total_games: int
    total_rounds: int
    games_by_playlist: dict[str, int]

    def to_table(self):
        table = [
            ["First game", self.first_game_starttime.date().isoformat()],
            ["Last game", self.last_game_starttime.date().isoformat()],
            ["Games total", self.total_games],
            ["Rounds total", self.total_rounds],
        ]
        for playlist, count in self.games_by_playlist.items():
            table.append([f"Games in playlist `{playlist}`", count])
        return table


class SummaryCollector:
    def __init__(self, conn: sqlite3.Connection, sqlite_collector: SqliteCollector):
        self.conn = conn
        assert sqlite_collector is not None

    def get_summary(self):
        game_count, round_count, first_game_time, last_game_time = self.conn.execute("""
            select 
                (select count(*) from game) as game_count,
                (select count(*) from round) as round_count,
                (select min(id) first_game from game) as first_game_time,
                (select max(id) last_game from game) as last_game_count
        """).fetchone()

        result = self.conn.execute("""
            select
                playlistCode,
                count(1) games_count
            from game
            group by playlistCode
            order by playlistCode
        """).fetchall()
        game_mode_count = OrderedDict()
        for game_mode, count in result:
            game_mode_count[game_mode] = count

        return Summary(
            first_game_starttime=datetime.datetime.utcfromtimestamp(first_game_time / 1000),
            last_game_starttime=datetime.datetime.utcfromtimestamp(last_game_time / 1000),
            total_games=game_count,
            total_rounds=round_count,
            games_by_playlist=game_mode_count
        )


class TestSummaryCollector:
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
