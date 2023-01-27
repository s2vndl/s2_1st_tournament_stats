from collections import defaultdict
from typing import List, Any

from s2_analytics.fris_analyzer import FriWeaponUsageAnalyzer


class MainWeaponAnalyzer:
    """
    Calculates main weapons used by a team based on kill log
    """

    def __init__(self, collected_weapons_groups: List[List[str]], teams: dict[str, List[str]]):
        self.team_by_player = {}
        self.teams = teams.keys()
        for team, players in teams.items():
            for player in players:
                self.team_by_player[player] = team
        self._analyzers: dict[str, FriWeaponUsageAnalyzer] = defaultdict(
            lambda: FriWeaponUsageAnalyzer(collected_weapons_groups))

    def process_kill(self, killer_id: str, weapon: str):
        self._analyzers[killer_id].process_kill(killer_id, weapon)

    def report(self) -> dict:
        main_weapons = {team: defaultdict(lambda: 0) for team in self.teams}
        for player in self.team_by_player:
            players_main_weapons = []
            for key, value in self._analyzers[player].report().items():
                if value > 0.5:
                    players_main_weapons.append(key)
            for weapon in players_main_weapons:
                main_weapons[self.team_by_player[player]][weapon] += 1
        return dict(main_weapons)
