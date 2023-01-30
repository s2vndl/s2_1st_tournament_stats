from collections import defaultdict
from datetime import datetime
from typing import List, Union

from s2_analytics.importer import RoundData, GameDetails, EventFlagCap, EventKill, EventData, RoundsEventData, Game

Timestamp = Union[datetime, int]


def _timestamp_to_datetime(value: Timestamp) -> datetime:
    return value if isinstance(value, datetime) else datetime.utcfromtimestamp(value / 1000)


class RoundBuilder:
    def __init__(self, game_id: int, round_number: int, start_time: Timestamp = None, end_time: int = None,
                 map: str = None):
        self.end_time = _timestamp_to_datetime(end_time)
        self.start_time = _timestamp_to_datetime(start_time)
        self.map = map
        self.score_red: int = 2
        self.score_blue: int = 3
        self.round_number = round_number
        self.game_id = game_id

    def build(self, scores: defaultdict[str, int]) -> RoundData:
        return RoundData(self.game_id, self.round_number, self.map, self.start_time, self.end_time, scores["Blue"],
                         scores["Red"])


class EventBuilder:
    killer: str
    victim: str
    weapon: str

    def __init__(self, killer: str, victim: str, weapon: str):
        self.victim = victim
        self.weapon = weapon
        self.killer = killer


class FakeClock:
    def __init__(self):
        self._current_fake_time = 1674928452000

    def get_millis(self) -> int:
        time = self._current_fake_time
        self.advance(2)
        return time

    def get_datetime(self) -> datetime:
        return datetime.utcfromtimestamp(self._current_fake_time / 1000)

    def advance(self, seconds):
        self._current_fake_time += seconds * 1000


clock = FakeClock()


class GameBuilder:
    def __init__(self, game_start_time: int = 0, teams: dict[str, list[str]] = None, factory=None,
                 match_quality: float = 0.8):
        self.match_quality = match_quality
        self.score: defaultdict[str, int] = defaultdict(lambda: 0)
        self.round_id = 0
        self.rounds: List[RoundData] = []
        self.round_in_progress: Union[None, RoundBuilder] = None
        self.events_by_round_num: RoundsEventData = []
        self.current_events: list[EventData] = []
        self.game_id = game_start_time
        self.teams = teams if teams is not None else {"Blue": ["A"], "Red": ["B"]}
        self.team_by_player = {}
        self.factory = factory
        for team, players in teams.items():
            for player in players:
                self.team_by_player[player] = team

    def add_round(self, start: int = 0, end_time: int = 0, map: str = "ctf_ash"):
        self._finish_round()
        self.round_in_progress = RoundBuilder(self.game_id, len(self.rounds) + 1, start_time=start,
                                              end_time=end_time, map=map)
        return self

    def _finish_round(self):
        if self.round_in_progress is not None:
            self.rounds.append(self.round_in_progress.build(self.score))
        self.score = defaultdict(lambda: 0)
        self.events_by_round_num.append([])

    def add_kill(self, time: Timestamp = 0, killer: str = None, victim: str = None,
                 weapon: str = None):
        if self.round_in_progress is None:
            raise ValueError("No round started yet")
        killer_team = self.team_by_player[killer] if killer is not None else None
        victim_team = self.team_by_player[victim] if victim is not None else None
        event = EventKill(self.game_id, self.round_in_progress.round_number, _timestamp_to_datetime(time),
                          killer, killer_team, victim, victim_team, weapon)
        self.events_by_round_num[-1].append(event)
        return self

    def add_cap(self, time: Timestamp = 0, player: str = None):
        team = self.team_by_player[player]
        self.score[team] += 1
        event = EventFlagCap(self.game_id, self.round_in_progress.round_number, _timestamp_to_datetime(time),
                             player, team)
        self.events_by_round_num[-1].append(event)
        return self

    def build(self) -> Union[Game, "GameBuilderFactory"]:
        self._finish_round()
        round_wins = defaultdict(lambda: 0)
        for round in self.rounds:
            round_wins[round.winner] += 1
        game = Game(GameDetails(self.game_id, datetime.utcfromtimestamp(self.game_id / 1000), "CTF-Standard-6",
                                round_wins["Blue"], round_wins["Red"], self.teams, self.match_quality), self.rounds,
                    self.events_by_round_num[:len(self.rounds)])
        if self.factory is not None:
            self.factory.finish_game(game)
            return self.factory
        else:
            return game


class GameBuilderFactory:
    def __init__(self, teams: dict[str, list[str]] = None):
        self.game_start = 0
        self._teams = teams
        self._clock = FakeClock()
        self._games = []

    def finish_game(self, game: Game):
        self._games.append(game)

    def add_game(self, match_quality=0.8, game_start_time: Timestamp = None) -> GameBuilder:
        if game_start_time is not None:
            self.game_start = game_start_time
        self.game_start += 1000
        return GameBuilder(teams=self._teams, factory=self, game_start_time=self.game_start,
                           match_quality=match_quality)

    def finish(self) -> List[Game]:
        return self._games
