from collections import defaultdict
from typing import List, Union, Set

from s2_analytics.fris_analyzer import FriWeaponUsageAnalyzer
from s2_analytics.importer import GameDetails, RoundData, EventData, EventKill


class MainWeaponAnalyzer:
    """
    Calculates main weapons used by a team based on kill log
    """

    def __init__(self, collected_weapons_groups: list[list[str]], teams: dict[str, list[str]]):
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
        mains = []
        for player in self.team_by_player:
            players_main_weapons = []
            for key, value in self._analyzers[player].report().items():
                if value > 0.5:
                    players_main_weapons.append(key)
            for weapon in players_main_weapons:
                team = self.team_by_player[player]
                mains.append(team + "/" + player + "/" + weapon)
                main_weapons[team][weapon] += 1

        result = {}
        for team in main_weapons:
            result[team] = dict(main_weapons[team])

        return result


class MainWeaponRoundTagger:
    def __init__(self, collected_weapons: list[list[str]]):
        self.analyzer: Union[MainWeaponAnalyzer, None] = None
        self.collected_weapons = collected_weapons
        self.round_tags_by_team = None

    def process_round(self, round: RoundData, game: GameDetails):
        if self.round_tags_by_team is not None:
            raise RuntimeError("tags were not collected after last round")
        if round.winner is not None:
            report = self.analyzer.report()
            self.round_tags_by_team = {}
            for team, main_weapons in report.items():
                team_tags = {}
                for weapon, count in main_weapons.items():
                    team_tags[f"{weapon}_x{count}"] = 1
                self.round_tags_by_team[team] = team_tags

        self.analyzer = None

    def process_event(self, event: EventData, round: RoundData, game: GameDetails):
        if self.analyzer is None:
            self.analyzer = MainWeaponAnalyzer(self.collected_weapons, game.teams)
        if isinstance(event, EventKill):
            self.analyzer.process_kill(event.killer_id, event.weapon)

    def get_team_round_tags(self) -> dict[str, Set[str]]:
        tags = self.round_tags_by_team
        self.round_tags_by_team = None
        return tags
