import datetime
import sqlite3
from collections import OrderedDict
from dataclasses import dataclass

from s2_analytics.collect.sqlite_collector import SqliteCollector


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


