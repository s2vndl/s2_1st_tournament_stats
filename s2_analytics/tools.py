import json
import os
from typing import List, Callable, Union

from IPython.core.display import Markdown
from IPython.core.display_functions import display
from pandas import DataFrame

from s2_analytics.collector.object_collector import GameObjectCollector
from s2_analytics.importer import JsonGameDeserializer, Processor, Game, RoundData, EventData, EventKill, EventFlagCap, \
    GameFilter


def dump_csv(df: DataFrame, id: str):
    csv_path = f"data/{id}.csv"
    csv_abs_path = f"{os.getcwd()}/build/markdown/{csv_path}"
    df.to_csv(csv_abs_path)
    display(Markdown(f"Chart data: [csv]({csv_path})"))


def _encode_event(e: EventData) -> dict:
    if isinstance(e, EventKill):
        return {
            "type": "PLAYER_KILL",
            "timestamp": to_long_timestamp(e.timestamp),
            "killerPlayfabId": e.killer_id,
            "killerTeam": e.killer_team,
            "victimPlayfabId": e.victim_id,
            "victimTeam": e.victim_team,
            "weaponName": e.weapon
        }
    elif isinstance(e, EventFlagCap):
        return {
            "type": "FLAG_CAP",
            "timestamp": to_long_timestamp(e.timestamp),
            "playfabId": e.capping_player_id,
            "cappingTeam": e.capping_team,
        }
    else:
        raise ValueError(f"Unsupported event type: `{e.__class__.__name__}`")


def _encode_round(rnd: RoundData, events: List[EventData]) -> dict:
    return {
        "startTime": to_long_timestamp(rnd.start_time),
        "endTime": to_long_timestamp(rnd.end_time),
        "mapName": rnd.map,
        "blueCaps": rnd.score_blue,
        "redCaps": rnd.score_red,
        "result": {
            "winner": rnd.winner,
            "isTie": rnd.is_tie
        },
        "events": [_encode_event(e) for e in events]
    }


def to_long_timestamp(time):
    return int(time.timestamp() * 1000)


def process_games(games: list[Game], processors: list[Processor], game_filters: Union[GameFilter, List[GameFilter]] = None):
    reader = JsonGameDeserializer(processors, game_filters)
    for game in games:
        game = dump_game_as_json_dict(game)
        reader.deserialize_game(game)


def dump_game_as_json_dict(game: Game):
    return {
        "playlistCode": game.details.playlist_code,
        "startTime": game.details.id,
        "teamRoundWins": game.team_round_wins,
        "teams": list(game.details.teams.keys()),
        "players": game.players,
        "rounds": [_encode_round(r, game.events_by_round[i]) for i, r in enumerate(game.rounds)],
        "matchQuality": game.details.match_quality,
        "teamWinProbabilities": game.details.team_win_probabilities
    }


def dump_games_as_json_dict(games: list[Game]):
    return [dump_game_as_json_dict(game) for game in games]


def process_game(path):
    with open(os.path.dirname(os.path.realpath(__file__)) + "/" + path, "r") as f:
        collector = GameObjectCollector()
        JsonGameDeserializer([collector]).deserialize_game(json.load(f))
        expected = collector.games[0]
    return expected
