import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join
from typing import Union, Protocol, List, Callable


@dataclass
class GameDetails:
    id: int
    start_time: datetime
    playlist_code: str
    score_blue: int
    score_red: int
    teams: dict[str, list[str]]
    match_quality: float
    team_win_probabilities: dict[str, float]

    @property
    def date_iso(self) -> str:
        return self.start_time.strftime('%Y-%m-%d')

    @property
    def winner(self) -> Union[None, str]:
        if self.score_red == self.score_blue:
            return None
        return "Red" if self.score_red > self.score_blue else "Blue"


@dataclass
class RoundData:
    game_id: int
    number: int
    map: str
    start_time: datetime
    end_time: datetime
    score_blue: int
    score_red: int

    @property
    def date_iso(self) -> str:
        return self.start_time.strftime('%Y-%m-%d')

    @property
    def winner(self) -> Union[None, str]:
        if self.score_red == self.score_blue:
            return None
        return "Red" if self.score_red > self.score_blue else "Blue"

    @property
    def is_tie(self) -> bool:
        return self.score_red == self.score_blue

    @property
    def id(self) -> str:
        return f"{self.game_id}-{self.number}"


class GameProcessor(Protocol):
    def process_game(self, game: GameDetails):
        ...


class RoundProcessor(Protocol):
    def process_round(self, round: RoundData, game: GameDetails):
        ...


class EventProcessor(Protocol):
    timestamp: datetime

    def process_event(self, event: "EventData", round: RoundData, game: GameDetails):
        ...


class FullProcessor(GameProcessor, RoundProcessor, EventProcessor):
    pass


Processor = Union[GameProcessor, RoundProcessor, EventProcessor]


@dataclass
class EventKill:
    game_id: int
    round_num: int
    timestamp: datetime
    killer_id: str
    killer_team: str
    victim_id: str
    victim_team: str
    weapon: str

    @property
    def date_iso(self) -> str:
        return self.timestamp.strftime('%Y-%m-%d')


@dataclass
class EventFlagCap:
    game_id: int
    round_num: int
    timestamp: datetime
    capping_player_id: str
    capping_team: str

    @property
    def date_iso(self) -> str:
        return self.timestamp.strftime('%Y-%m-%d')


EventData = Union[EventFlagCap, EventKill]
RoundsEventData = List[List[EventData]]
GameFilter = Callable[[GameDetails], bool]


@dataclass
class Game:
    details: GameDetails
    rounds: List[RoundData]
    events_by_round: RoundsEventData

    @property
    def team_round_wins(self):
        return {"Blue": self.details.score_blue,
                "Red": self.details.score_red}

    @property
    def players(self):
        players = []
        for team, team_players in self.details.teams.items():
            for tp in team_players:
                players.append({"displayName": tp, "playfabId": tp, "team": team})
        return players


def import_games(logs_dir: str, period_days: int = 60, start_date=None, end_date=None,
                 processors: List[Union[GameProcessor, EventProcessor, RoundProcessor]] = None,
                 game_filters: List[GameFilter] = None
                 ):
    decoder = JsonGameDeserializer(processors, game_filters=game_filters)
    for game_json in read_games_dir(logs_dir, period_days, start_date, end_date):
        decoder.deserialize_game(game_json)


def _has_method(obj, method):
    return callable(getattr(obj, method, None))


def read_games_dir(logs_dir: str, period_days: int = 60, start_date: datetime = None, end_date: datetime = None):
    if start_date is None:
        start_date = datetime.today() - timedelta(days=period_days)
    if end_date is None:
        end_date = datetime.today() + timedelta(days=1)
    games = _read_games_json(logs_dir, start_date, end_date)

    for gameData in games:
        yield gameData


def _read_games_json(logs_dir, start_timestamp: datetime, end_timestamp: datetime):
    logs = [f for f in listdir(logs_dir) if isfile(join(logs_dir, f))]
    games = []
    for log in logs:
        match = re.match("^game_([0-9]{13}).json", log)
        if not match:
            continue
        timestamp = int(match.group(1))
        game_start_time = datetime.utcfromtimestamp(timestamp / 1000)
        if game_start_time < start_timestamp:
            continue
        if game_start_time > end_timestamp:
            continue
        with open(logs_dir + "/" + log, "r") as f:
            games.append(json.load(f))
    return games


class JsonGameDeserializer:
    def __init__(self, processors: list[Union[GameProcessor, RoundProcessor, EventProcessor]] = None,
                 game_filters: Union[GameFilter, List[GameFilter]] = None):
        game_filters = game_filters if game_filters is not None else []
        self.game_filters = game_filters if isinstance(game_filters, list) else [game_filters]
        if processors is None:
            processors = []
        self.game_processors = [p for p in processors if _has_method(p, "process_game")]
        self.round_processors = [p for p in processors if _has_method(p, "process_round")]
        self.event_processors = [p for p in processors if _has_method(p, "process_event")]

    def deserialize_games(self, game_json_datas: list[dict]):
        for data in game_json_datas:
            self.deserialize_game(data)

    def deserialize_game(self, game_json_data: dict):
        try:
            game: GameDetails = self._decode_game(game_json_data)
        except NotImplementedError as e:
            return
        if all([f(game) for f in self.game_filters]):
            for i, round_data in enumerate(game_json_data["rounds"]):
                round = self._decode_round(i + 1, round_data, game)
                for event_data in round_data["events"]:
                    if len(self.event_processors) > 0:
                        event = self._decode_event(event_data, round, game)
                        for processor in self.event_processors:
                            processor.process_event(event, round, game)

                for processor in self.round_processors:
                    processor.process_round(round, game)

            for processor in self.game_processors:
                processor.process_game(game)

    def _decode_event(self, data: dict, round: RoundData, game: GameDetails) -> EventData:
        if data["type"] == "PLAYER_KILL":
            value = data["timestamp"]
            return EventKill(
                game.id,
                round.number,
                datetime.utcfromtimestamp(value / 1000),
                data["killerPlayfabId"],
                data["killerTeam"],
                data["victimPlayfabId"],
                data["victimTeam"],
                data["weaponName"]
            )
        elif data["type"] == "FLAG_CAP":
            return EventFlagCap(
                game.id,
                round.number,
                datetime.utcfromtimestamp(data["timestamp"] / 1000),
                data["playfabId"],
                data["cappingTeam"],
            )

    def _decode_round(self, number: int, round: dict, game: GameDetails) -> RoundData:
        return RoundData(
            game.id,
            number,
            round["mapName"],
            datetime.utcfromtimestamp(round["startTime"] / 1000),
            datetime.utcfromtimestamp(round["endTime"] / 1000),
            round["blueCaps"],
            round["redCaps"]
        )

    def _decode_game(self, data: dict) -> GameDetails:
        playlist_code = data["playlistCode"]
        if "Red" not in data["teamRoundWins"]:
            raise NotImplementedError("no support for custom team names: " + ", ".join(data["teamRoundWins"]))
        score_red: int = data["teamRoundWins"]["Red"]
        score_blue: int = data["teamRoundWins"]["Blue"]
        teams = defaultdict(lambda: [])
        for player in data["players"]:
            teams[player["team"]].append(player["playfabId"])
        return GameDetails(
            data["startTime"],
            datetime.utcfromtimestamp(data["startTime"] / 1000),
            playlist_code,
            score_blue,
            score_red,
            dict(teams),
            data["matchQuality"],
            data["teamWinProbabilities"]
        )
