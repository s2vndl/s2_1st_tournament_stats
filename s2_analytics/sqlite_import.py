import re
import tempfile
import uuid
from typing import Union

import atexit
import os
import json
import sqlite3
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join, exists

from s2_analytics.constants import WEAPONS_PRIMARY, WEAPONS_SECONDARY
from s2_analytics.fris_analyzer import FriWeaponUsageAnalyzer


def _register_cleanup(sqlite_path):
    def delete_if_exists(path):
        if exists(path):
            os.remove(path)

    atexit.register(delete_if_exists, sqlite_path)


def import_games(logs_dir: str, sqlite_path: Union[str, None] = None, period_days: int = 60):
    game_importer = GameImporter()
    game_importer.import_games(logs_dir, sqlite_path, period_days)
    return game_importer.con, game_importer.con.cursor()


def _prepare_sqlite_db(sqlite_path: Union[None, str]):
    if sqlite_path is None:
        sqlite_path = tempfile.gettempdir() + f"/s2_analytics_{uuid.uuid4()}.sqlite"
    if exists(sqlite_path):
        os.remove(sqlite_path)
    con = sqlite3.connect(sqlite_path)
    _register_cleanup(sqlite_path)
    return con


def _read_games_json(logs_dir, start_timestamp: datetime):
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
        with open(logs_dir + "/" + log, "r") as f:
            games.append(json.load(f))
    return games


class GameImporter:
    def __init__(self):
        self.cur = None
        self.con = None

    def import_games(self, logs_dir: str, sqlite_path: Union[str, None] = None, period_days: int = 60):
        start_date = datetime.today() - timedelta(days=period_days)
        games = _read_games_json(logs_dir, start_date)
        self.con = _prepare_sqlite_db(sqlite_path)
        self.cur = self.con.cursor()

        self._create_tables()

        supported_playlist_code = ["CTF-Standard-4", "CTF-Standard-6", "CTF-Standard-8"]
        for game in games:
            game_date = datetime.utcfromtimestamp(game["startTime"] / 1000)
            if game["playlistCode"] not in supported_playlist_code:
                continue
            game["redRoundWins"] = game["teamRoundWins"]["Red"]
            game["blueRoundWins"] = game["teamRoundWins"]["Blue"]
            game["winner"] = game["result"]["winner"]
            game["date"] = game_date.strftime('%Y-%m-%d')
            self.cur.execute("""
                insert into game 
                    values (:startTime, :date, :playlistCode, :redRoundWins, :blueRoundWins, :winner)
            """, game)
            rounds_raw = game["rounds"]
            self._insert_rounds(self.cur, game, rounds_raw)
        self.con.commit()

    def _create_tables(self):
        create_table_queries = """
            CREATE TABLE game ('id', 'date', playlistCode'', 'redRoundWins', 'blueRoundWins', 'winner')
            CREATE TABLE round ('id', 'game', 'date', 'round', 'mapName', 'startTime', 'endTime', 'blueCaps', 'redCaps', 'result')
            CREATE TABLE event_kill ('game', 'round', 'timestamp', 'date', 'killerPlayfabId', 'killerTeam', 'victimPlayfabId', 'victimTeam', 'weaponName')
            CREATE TABLE event_cap ('game', 'round', 'mapName', 'timestamp', 'cappingTeam', 'playfabId', 'millisSinceStart')
            CREATE TABLE weapon_usage ("round_id", "date", "weapon", "usage")
        """
        for query in create_table_queries.strip().split("\n"):
            self.cur.execute(query)

    def _insert_rounds(self, cur, game_data, rounds_raw):
        round_id = 0
        for round_no, round in enumerate(rounds_raw):
            analyzer = FriWeaponUsageAnalyzer([WEAPONS_PRIMARY, WEAPONS_SECONDARY])
            round_id += 1
            round = round
            round["round"] = round_no
            round["id"] = round_id
            round["date"] = game_data["date"]
            round["game"] = game_data["startTime"]
            caps_diff = round["redCaps"] - round["blueCaps"]
            round["result"] = "tie" if caps_diff == 0 else ("redWins" if caps_diff > 0 else "blueWins")
            cur.execute("""
                insert into round 
                    values (:id, :game, :date, :round, :mapName, :startTime, 
                        :endTime, :blueCaps, :redCaps, :result) 
            """, round)
            self._insert_events(round["events"], game_data, round, analyzer)
            self._insert_weapon_usage_data(analyzer, round)

    def _insert_weapon_usage_data(self, analyzer, round_data):
        report = analyzer.report()
        for weapon, usage_ratio in report.items():
            usage = {
                "round_id": round_data["id"],
                "date": round_data["date"],
                "weapon": weapon,
                "usage": usage_ratio
            }
            self.cur.execute("""
                    insert into weapon_usage 
                        values (:round_id, :date, :weapon, :usage) 
                    """, usage)

    def _insert_events(self, events_data, game_data, round_data, analyzer: FriWeaponUsageAnalyzer):
        for event in events_data:
            row = dict(event)
            del row["type"]

            if event["type"] == "PLAYER_KILL":
                analyzer.process_kill(event["killerPlayfabId"], event["weaponName"])
                row["game"] = game_data["startTime"]
                row["round_id"] = round_data["id"]
                row["round"] = round_data["round"]
                row["date"] = datetime.utcfromtimestamp(row["timestamp"] / 1000).strftime('%Y-%m-%d')
                self.cur.execute("""
                    insert into event_kill 
                        values (:game, :round, :timestamp, :date, :killerPlayfabId, 
                            :killerTeam, :victimPlayfabId, :victimTeam, :weaponName)
                    """, row)
            elif event["type"] == "FLAG_CAP":
                row["game"] = game_data["startTime"]
                row["mapName"] = round_data["mapName"]
                row["round"] = round_data["round"]
                row["millisSinceStart"] = event["timestamp"] - round_data["startTime"]
                self.cur.execute("""
                    insert into event_cap 
                        values (:game, :round, :mapName, :timestamp,
                            :cappingTeam, :playfabId, :millisSinceStart)
                    """, row)
