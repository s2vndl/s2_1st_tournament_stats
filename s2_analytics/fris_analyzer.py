from collections import defaultdict
from typing import List, Any


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

    def report(self) -> defaultdict[str, float]:
        totals = defaultdict(lambda: 0.)
        for group_id, group in enumerate(self.collected_weapons_groups):
            for weapon in group:
                for player_stats in self.kills[group_id].values():
                    totals[weapon] += player_stats[weapon] / sum(player_stats.values())
        return totals
