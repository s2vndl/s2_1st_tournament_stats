import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join
from typing import Union, Protocol, List


@dataclass
class GameData:
    id: int
    start_time: datetime
    playlistCode: str
    score_red: int
    score_blue: int

    @property
    def date_iso(self) -> str:
        return self.start_time.strftime('%Y-%m-%d')

    @property
    def winner(self) -> Union[None, str]:
        if self.score_red == self.score_blue:
            return None
        return "Red" if self.score_red > self.score_blue else "Blue"


class EventData(Protocol):
    pass


@dataclass
class RoundData:
    game_id: int
    number: int
    map: str
    start_time: datetime
    start_millis: int
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
    def id(self) -> str:
        return f"{self.game_id}-{self.number}"


class GameProcessor(Protocol):
    def process_game(self, game: GameData):
        ...

    def finalize_game_processing(self):
        pass


class RoundProcessor(Protocol):
    def process_round(self, round: RoundData, game: GameData):
        ...


class EventProcessor(Protocol):
    timestamp: datetime

    def process_event(self, event: EventData, round: RoundData, game: GameData):
        ...


class FullProcessor(GameProcessor, RoundProcessor, EventProcessor):
    pass


@dataclass
class EventKill(EventData):
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
class EventFlagCap(EventData):
    game_id: int
    round_num: int
    timestamp: datetime
    millis_since_start: int
    capping_player_id: str
    capping_team: str

    @property
    def date_iso(self) -> str:
        return self.timestamp.strftime('%Y-%m-%d')


def import_games(logs_dir: str, period_days: int = 60,
                 processors: List[Union[GameProcessor, EventProcessor, RoundProcessor]] = None) -> List[GameData]:

    def has_method(obj, method):
        return callable(getattr(obj, method, None))

    game_processors = [p for p in processors if has_method(p, "process_game")]
    round_processors = [p for p in processors if has_method(p, "process_round")]
    event_processors = [p for p in processors if has_method(p, "process_event")]

    game_importer = GameImporter(game_processors, round_processors, event_processors)
    return game_importer.import_games(logs_dir, period_days)


class GameImporter:
    def __init__(self, game_processors: List[GameProcessor], round_processors: List[RoundProcessor],
                 event_processors: List[EventProcessor]):
        self.game_processors = game_processors
        self.round_processors = round_processors
        self.event_processors = event_processors

    def import_games(self, logs_dir: str, period_days: int = 60) -> List[GameData]:
        start_date = datetime.today() - timedelta(days=period_days)
        games = self._read_games_json(logs_dir, start_date)

        supported_playlist_code = ["CTF-Standard-4", "CTF-Standard-6", "CTF-Standard-8"]
        result = []
        for gameData in games:
            if gameData['playlistCode'] not in supported_playlist_code:
                continue
            try:
                game = self._decode_game(gameData)
            except NotImplementedError as e:
                print(e)
                continue


            for i, round_data in enumerate(gameData["rounds"]):
                round = self._decode_round(i, round_data, game)

                for event_data in round_data["events"]:
                    for processor in self.event_processors:
                        processor.process_event(self._decode_event(event_data, round, game), round, game)

                for processor in self.round_processors:
                    processor.process_round(round, game)

            result.append(game)
            for processor in self.game_processors:
                processor.process_game(game)
        for processor in self.game_processors:
            processor.finalize_game_processing()

        return result

    def _read_games_json(self, logs_dir, start_timestamp: datetime):
        logs = [f for f in listdir(logs_dir) if isfile(join(logs_dir, f))]
        games = []
        for log in logs:
            match = re.match("^game_([0-9]{13}).json", log)
            if not match:
                continue
            timestamp = int(match.group(1))
            game_start_time = self._js_millis_to_datetime(timestamp)
            if game_start_time < start_timestamp:
                continue
            with open(logs_dir + "/" + log, "r") as f:
                games.append(json.load(f))
        return games

    def _decode_event(self, data: dict, round: RoundData, game: GameData) -> EventData:
        if data["type"] == "PLAYER_KILL":
            return EventKill(
                game.id,
                round.number,
                self._js_millis_to_datetime(data["timestamp"]),
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
                self._js_millis_to_datetime(data["timestamp"]),
                data["timestamp"] - round.start_millis,
                data["playfabId"],
                data["cappingTeam"],
            )

    def _js_millis_to_datetime(self, value):
        return datetime.utcfromtimestamp(value / 1000)

    def _decode_round(self, number: int, round: dict, game: GameData) -> RoundData:
        return RoundData(
            game.id,
            number,
            round["mapName"],
            self._js_millis_to_datetime(round["startTime"]),
            round["startTime"],
            self._js_millis_to_datetime(round["endTime"]),
            round["redCaps"],
            round["blueCaps"]
        )

    def _decode_game(self, data: dict):
        playlist_code = data["playlistCode"]
        if "Red" not in data["teamRoundWins"]:
            raise NotImplementedError("no support for custom team names: " + ", ".join(data["teamRoundWins"]))
        score_red: int = data["teamRoundWins"]["Red"]
        score_blue: int = data["teamRoundWins"]["Blue"]
        return GameData(
            data["startTime"],
            datetime.utcfromtimestamp(data["startTime"] / 1000),
            playlist_code,
            score_red,
            score_blue
        )
