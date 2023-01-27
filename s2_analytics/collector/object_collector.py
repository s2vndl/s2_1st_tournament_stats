from typing import List

from s2_analytics.importer import GameProcessor, RoundProcessor, EventProcessor, GameData, RoundData, EventData


class ObjectCollector(GameProcessor, RoundProcessor, EventProcessor):
    def __init__(self):
        self.games: List[GameData] = []
        self.rounds: List[RoundData] = []
        self.events: List[EventData] = []

    def process_game(self, game: GameData):
        self.games.append(game)

    def process_round(self, round: RoundData, game: GameData):
        self.rounds.append(round)

    def process_event(self, event: EventData, round: RoundData, game: GameData):
        self.events.append(event)
