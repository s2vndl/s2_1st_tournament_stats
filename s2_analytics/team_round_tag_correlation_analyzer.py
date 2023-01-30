from typing import Callable, Union

import pandas as pd

from s2_analytics.importer import RoundData, GameDetails, EventData


class TeamRoundTagCorrelationAnalyzer:
    def __init__(self, taggers, round_filter: Union[Callable[[RoundData], bool], None] = None):
        self.round_filter = round_filter if round_filter is not None else lambda r: True
        self.taggers = taggers
        self.tags_by_round: list[dict[str, int]] = []

    def process_round(self, round: RoundData, game: GameDetails):
        if not self.round_filter(round):
            return
        for t in self.taggers:
            t.process_round(round, game)
            round_tags = t.get_team_round_tags()
            if round_tags is not None:
                for team, tags in round_tags.items():
                    team_tags = {}
                    for tag in tags:
                        team_tags[tag] = 1
                    team_tags["win"] = 1 if round.winner == team else 0
                    self.tags_by_round.append(team_tags)

    def process_event(self, event: EventData, round: RoundData, game: GameDetails):
        if not self.round_filter(round):
            return
        for t in self.taggers:
            t.process_event(event, round, game)

    def calculate_win_correlation(self):
        data = pd.DataFrame.from_dict(self.tags_by_round) \
            .fillna(0) \
            .corr()["win"] \
            .to_dict()

        del data["win"]
        return data
