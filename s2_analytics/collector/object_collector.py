from typing import List, Union

from s2_analytics.importer import GameProcessor, RoundProcessor, EventProcessor, GameDetails, RoundData, EventData, \
    RoundsEventData, Game


class GameObjectCollector(GameProcessor, RoundProcessor, EventProcessor):
    def __init__(self):
        self.games: List[Game] = []
        self.rounds: List[RoundData] = []
        self.events: RoundsEventData = []

    def process_game(self, game_details: GameDetails):
        self.games.append(Game(game_details, self.rounds, self.events))

    def process_round(self, round: RoundData, game: GameDetails):
        self.rounds.append(round)

    def process_event(self, event: EventData, round: RoundData, game: GameDetails):
        while len(self.events) < round.number:
            self.events.append([])
        self.events[round.number-1].append(event)
