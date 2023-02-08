import sqlite3
from collections import defaultdict
from typing import List, Set

import pandas as pd

from s2_analytics.constants import WEAPONS_PRIMARY, WEAPONS_SECONDARY
from s2_analytics.importer import EventProcessor, EventData, RoundData, GameDetails, EventKill, RoundProcessor


class FriWeaponUsageAnalyzer:
    """
    calculates weapon usage with formula weaponkills/allkills as suggested by Fri
    https://discord.com/channels/498800300199772162/977172055361470474/1063083053003583548
    """

    def __init__(self, collected_weapons_groups: List[List[str]]):
        self.collected_weapons_groups = collected_weapons_groups

        # nested dictionaries: weapongroup -> player -> weapon
        self.kills = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))

    def process_kill(self, killer_id: str, weapon: str):
        for i, weapons_in_group in enumerate(self.collected_weapons_groups):
            if weapon not in weapons_in_group:
                continue
            self.kills[i][killer_id][weapon] += 1

    def report(self) -> dict[str, float]:
        totals = defaultdict(lambda: 0.)
        for group_id, group in enumerate(self.collected_weapons_groups):
            for weapon in group:
                for player_stats in self.kills[group_id].values():
                    totals[weapon] += player_stats[weapon] / sum(player_stats.values())
        return dict(totals)


class FriWeaponUsageCollector(EventProcessor, RoundProcessor):
    analyzer: FriWeaponUsageAnalyzer
    last_round: RoundData = None
    dates: Set[str] = set()

    def process_round(self, round: RoundData, game: GameDetails):
        report = self.analyzer.report()
        self._store_data(round.id, round.date_iso, report)
        self.analyzer = self._create_analyzer()

    def __init__(self):
        self.con: sqlite3.Connection = sqlite3.connect("file::memory:")
        self.finalized = False
        self.cur: sqlite3.Cursor = self.con.cursor()
        self.analyzer = self._create_analyzer()

    def init(self) -> "FriWeaponUsageCollector":
        self.cur.execute('CREATE TABLE weapon_usage ("round_id", "date", "weapon", "usage")')
        self.cur.execute('CREATE TABLE weapon_usage_dates("date")')
        self.cur.execute('CREATE TABLE weapon_usage_rounds("id", "date")')
        self.cur.execute('CREATE TABLE weapon_usage_weapons("weapon")')
        return self

    def process_event(self, event: EventData, round: RoundData, game: GameDetails):
        if self.finalized:
            raise RuntimeError("collect is already finalized")

        self.dates.add(round.date_iso)
        if isinstance(event, EventKill):
            self.analyzer.process_kill(event.killer_id, event.weapon)

    def _create_analyzer(self):
        return FriWeaponUsageAnalyzer([WEAPONS_PRIMARY, WEAPONS_SECONDARY])

    def _store_data(self, round_id: str, date_iso: str, analyzer_report: dict):
        for weapon, usage_ratio in analyzer_report.items():
            self.cur.execute("""
                insert into weapon_usage 
                    values (:round_id, :date, :weapon, :usage) 
                """, {
                "round_id": round_id,
                "date": date_iso,
                "weapon": weapon,
                "usage": usage_ratio
            })
            self.cur.execute("""
                insert into weapon_usage_rounds 
                    values (:round_id, :date) 
                """, {
                "round_id": round_id,
                "date": date_iso
            })

    def _finalize(self):
        if self.finalized:
            return
        self.finalized = True
        for date in sorted(self.dates):
            self.cur.execute(f"insert into weapon_usage_dates values(?)", [date])
        for weapon in WEAPONS_PRIMARY + WEAPONS_SECONDARY:
            self.cur.execute(f"insert into weapon_usage_weapons values(?)", [weapon])

        self.cur.execute("""
            create table weapon_usage_by_date as
                select dw.date, dw.weapon, sum(wu.usage)/(select count(1) from weapon_usage_rounds as round where round.date = dw.date) as usage
                from
                -- all date+weapon combinations
                    (select * from (select date from weapon_usage_dates)
                             cross join (select weapon from weapon_usage_weapons)) dw
        
                left outer join weapon_usage wu on wu.date = dw.date and wu.weapon = dw.weapon
                group by dw.date, dw.weapon
                order by dw.date, sum(wu.usage) desc, dw.weapon
            """)
        self.con.commit()

    def get_data(self, weapons_list, avg_period_days: int, min_days: int, total_period_days: int):
        self._finalize()
        weapons_list_str = ", ".join([f"'{x}'" for x in weapons_list])

        df = pd.read_sql_query(f"""
                select
                weapon,
                date,
                100.0 * usage /
                    (select sum(usage)
                        from weapon_usage_by_date wu2
                        where wu.date = wu2.date and weapon in ({weapons_list_str})
                    ) as usage
            from weapon_usage_by_date wu
                where date >= datetime((select max(date) from weapon_usage_by_date), '-{total_period_days} days')
                and weapon in ({weapons_list_str})
            order by weapon asc
        """, con=self.con, parse_dates="date")
        df["usage percentage"] = df.groupby("weapon", as_index=False, group_keys=False) \
            .apply(
            lambda grp, freq: grp.rolling(freq, on='date', min_periods=min_days)['usage'].mean(),
            f"{avg_period_days}D")
        return df
