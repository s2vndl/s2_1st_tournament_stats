import datetime
import os
import re
import json
from os.path import exists
from sys import argv
from typing import Callable, List

import requests

GAME_FILE_PATTERN = "^game_([0-9]{13}).json$"


def fetch_games_start_times() -> List[int]:
    print("fetching list of games")
    response = requests.get("http://78.47.147.210:9000/api/v1/game/start_times")
    if response.status_code != 200:
        raise ValueError(f"Expected response with status 200 but got {response.status_code}")
    return json.loads(response.content)


def fetch_game_as_json(start_time) -> str:
    response = requests.get(f"http://78.47.147.210:9000/api/v1/game/{start_time}?withEvents=true")
    if response.status_code != 200:
        raise ValueError(f"Expected response with status 200 but got {response.status_code}")
    return response.content.decode()


def exit_with_error(message: str):
    print(message)
    exit(1)


class GamesRepo:
    def __init__(self, dir):
        self.dir = dir

    def find_games(self, dir: str, game_id_consumer: Callable[[int], None]):
        for file in os.listdir(dir):
            match = re.match(GAME_FILE_PATTERN, file)
            if not match or not os.path.isfile(dir + "/" + file):
                continue
            start_time = int(match.group(1))
            game_id_consumer(start_time)

    def save(self, game_id: int, json_content: str):
        filename = self._get_filename(game_id)
        with open(filename, "w") as f:
            f.write(json_content)

    def remove_games(self, dir, games_to_delete):
        for game in games_to_delete:
            filename = self._get_filename(game)
            os.unlink(filename)
            print("Removed " + filename)
        pass

    def _get_filename(self, game_id):
        filename = f"{self.dir}/game_{game_id}.json"
        return filename


if __name__ == "__main__":
    if len(argv) != 2:
        exit_with_error(f"Target directory required.\n"
                        f"Usage: python {os.path.basename(__file__)} TARGET_DIR")
    dir = argv[1]
    if not exists(dir):
        exit_with_error(f"Target directory does not exist: {dir}")

    if not os.path.isdir(dir):
        exit_with_error(f"Target is not a directory: {dir}")

    start_timestamp = int(datetime.datetime.fromisoformat("1970-01-01").timestamp() * 1000)
    print(f"cut_off: {start_timestamp}")
    games_to_download = fetch_games_start_times()
    print(f"found ids of {len(games_to_download)} games")
    games_to_download = [id for id in games_to_download if int(id) >= int(start_timestamp)]

    games_to_delete = []
    repo = GamesRepo(dir)
    def on_found_local_game(start_time):
        if start_time in games_to_download:
            games_to_download.remove(start_time)
        else:
            games_to_delete.append(start_time)

    repo.find_games(dir, on_found_local_game)

    if len(games_to_delete) > 0:
        print(f"Found {len(games_to_delete)} games to delete")
        repo.remove_games(dir, games_to_delete)

    print(f"{len(games_to_download)} games to download: {games_to_download}")

    for i, game_id in enumerate(games_to_download):
        game_json = fetch_game_as_json(game_id)
        repo.save(game_id, game_json)
        if i % 5 == 4:
            print(f"Progress: {i + 1}/{len(games_to_download)}")
