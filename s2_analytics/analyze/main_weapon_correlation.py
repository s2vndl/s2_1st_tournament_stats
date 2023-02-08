import sqlite3
from collections import defaultdict, namedtuple
from typing import Callable, Union

import pandas as pd

from s2_analytics.collect.sqlite_collector import SqliteCollector
from s2_analytics.importer import RoundData, GameDetails, EventData

Correlation = namedtuple("Correlation", ["correlation", "sample_count"])


class OneWeaponCorrelations:
    def __init__(self, tag: str, correlations_by_map: dict[str, Correlation]):
        self.tag = tag
        self._total_samples = 0
        for correlation in correlations_by_map.values():
            assert isinstance(correlation.sample_count, int)
            assert 0 <= correlation.sample_count
            assert isinstance(correlation.correlation, float)
            assert -1.0 <= correlation.correlation <= 1.0
            self._total_samples += correlation.sample_count
        self._correlations_by_map = correlations_by_map

    @property
    def maps(self) -> list[str]:
        return list(self._correlations_by_map.keys())

    def correlation(self, map: str) -> float:
        return self._correlations_by_map[map].correlation if map in self._correlations_by_map else 0.0

    def sample_count(self, map: Union[str, None] = None):
        if map is None:
            return self._total_samples
        elif map not in self._correlations_by_map:
            return 0
        else:
            return self._correlations_by_map[map].sample_count

    def filter(self, min_samples):
        return OneWeaponCorrelations(self.tag, {map: data for map, data in self._correlations_by_map.items() if data.sample_count >= min_samples})


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

    def tag_counts(self, tag_filter: Callable[[str], bool] = None, map_name=None):
        if tag_filter is None:
            tag_filter = lambda t: True
        where_clause = ""
        if map_name is not None:
            where_clause = f"where mapName = '{map_name}'"

        fetchall = self.cursor.execute(f"""
               select tag, count(*) as count 
               from team_round_tag trt
                   join round r on r.game = trt.game and r.round = trt.round
                   {where_clause}
               group by trt.tag 
               """).fetchall()
        return {tag: count for tag, count in fetchall if tag_filter(tag)}

    def calculate_win_correlation(self, map_name=None, weapon_name=None):
        round_filters = []
        if map_name is not None:
            round_filters.append(f"r.mapName = '{map_name}'")
        if weapon_name is not None:
            round_filters.append(f"trt.tag in ('win', 'lose', '{weapon_name}')")
        filter_query = " AND ".join(round_filters)
        where_clause = "" if filter_query == "" else " WHERE " + filter_query
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

    def correlations_for_weapon_tag(self, weapon_tag) -> OneWeaponCorrelations:
        q = f"""
            select r.mapName, group_concat(tag, ';') as tags 
            from team_round_tag trt
                join round r on r.game = trt.game and r.round = trt.round
                 WHERE trt.tag in ('win', 'lose', '{weapon_tag}')
            group by trt.game, trt.round, trt.team 
            """
        resultset = self.cursor.execute(q)
        cols = set()
        pd_dicts = defaultdict(lambda: [])
        fetchall = resultset.fetchall()
        for row in fetchall:
            row_dict = {}
            for tag in row[1].split(";"):
                cols.add(tag)
                row_dict[tag] = 1.0
            pd_dicts[row[0]].append(row_dict)
        result = {}
        for map in pd_dicts.keys():
            df = pd.DataFrame.from_records(pd_dicts[map])

            sample_count = int(df[weapon_tag].value_counts()[1]) if weapon_tag in df else 0
            data = df.fillna(0).corr()["win"].to_dict()
            del data["win"]
            del data["lose"]

            result[map] = Correlation(data[weapon_tag] if weapon_tag in data else 0.0, sample_count)
        return OneWeaponCorrelations(weapon_tag, result)

    def calculate_win_correlation_per_map(self):
        resultset = self.cursor.execute(f"""
            select distinct mapName from round
            """).fetchall()
        results = {}
        for map, in resultset:
            results[map] = self.calculate_win_correlation(map)
        return results

    def _iter_all_maps(self):
        resultset = self.cursor.execute(f"""
            select distinct mapName from round
            """).fetchall()
        results = {}
        for map, in resultset:
            yield map

    def tag_counts_per_map(self, tag_filter: Callable[[str], bool] = None):
        result = {}
        for map in self._iter_all_maps():
            result[map] = self.tag_counts(tag_filter, map)

        return result
