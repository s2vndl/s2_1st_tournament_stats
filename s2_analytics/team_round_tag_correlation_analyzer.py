import sqlite3
from typing import Callable, Union

import pandas as pd
from numpy import int64

from s2_analytics.collector.sqlite_collector import SqliteCollector
from s2_analytics.importer import RoundData, GameDetails, EventData


class TeamRoundTagCorrelationAnalyzer:
    def __init__(self, conn: sqlite3.Connection, sqlite_collector: SqliteCollector, taggers,
                 round_filter: Union[Callable[[RoundData], bool], None] = None):
        assert sqlite_collector is not None  # ensure dependency met; its tables are used in sqlite queries
        self.round_filter = round_filter if round_filter is not None else lambda r: True
        self.taggers = taggers
        self.connection = conn
        self.cursor = self.connection.cursor()

    def init(self) -> "TeamRoundTagCorrelationAnalyzer":
        self._create_tables()
        return self

    def _create_tables(self):
        queries = """
                CREATE TABLE team_round_tag ("game", "round", "team", "tag");
            """
        for query in queries.strip().split("\n"):
            self.cursor.execute(query.rstrip(";"))

    def process_round(self, round: RoundData, game: GameDetails):
        if not self.round_filter(round):
            return
        for t in self.taggers:
            t.process_round(round, game)
            round_tags = t.get_team_round_tags()
            if round_tags is not None:
                for team in ["Red", "Blue"]:
                    tags = round_tags[team]
                    team_tags = []
                    for tag in tags:
                        team_tags.append(tag)
                    if round.winner == team:
                        team_tags.append("win")
                    else:
                        team_tags.append("lose")
                    if len(team_tags) == 0:
                        raise ValueError("each team-round should have at least one entry for joins")
                    if len(set(team_tags)) != len(team_tags):
                        raise AssertionError("team tags are supposed to be unique at this point")
                    for tag in team_tags:
                        self.cursor.execute("""
                           insert into team_round_tag values (:game, :round, :team, :tag)
                        """, {"game": game.id, "round": round.number, "team": team, "tag": tag})
        self.connection.commit()

    def process_event(self, event: EventData, round: RoundData, game: GameDetails):
        if not self.round_filter(round):
            return
        for t in self.taggers:
            t.process_event(event, round, game)

    def tags_by_round(self, tag_filter: Callable[[str], bool] = None):
        if tag_filter is None:
            tag_filter = lambda t: True
        fetchall = self.cursor.execute("""
                           select * from team_round_tag
                        """).fetchall()
        r = []
        for t in fetchall:
            if tag_filter(t[3]):
                r.append(t)
        return r

    def calculate_win_correlation(self, round_filter_sql: Union[str, list[str]] = None):
        if isinstance(round_filter_sql, str):
            round_filter_sql = [round_filter_sql]
        where_clause = "" if round_filter_sql is None else "WHERE " + " AND ".join(round_filter_sql)
        resultset = self.cursor.execute(f"""
            select group_concat(tag, ';') as tags 
            from team_round_tag trt
                join round r on r.game = trt.game and r.round = trt.round
                {where_clause}
            group by trt.game, trt.round, trt.team 
            """)
        cols = set()
        pd_dicts = []
        fetchall = resultset.fetchall()
        for row in fetchall:
            row_dict = {}
            for tag in row[0].split(";"):
                cols.add(tag)
                row_dict[tag] = 1.0
            pd_dicts.append(row_dict)
        from_dict = pd.DataFrame.from_records(pd_dicts)
        fillna = from_dict \
            .fillna(0)
        corr = fillna.corr()
        data = corr["win"] \
            .to_dict()

        del data["win"]
        del data["lose"]
        return data
