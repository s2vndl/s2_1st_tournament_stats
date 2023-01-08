import os
import json
from datetime import datetime

from os import listdir
from os.path import isfile, join, exists

PREPARE_TABLES_QUERIES = """
CREATE TABLE game ('id', 'date', playlistCode'', 'redRoundWins', 'blueRoundWins', 'winner')
CREATE TABLE round ('game', 'date', 'round', 'mapName', 'startTime', 'endTime', 'blueCaps', 'redCaps', 'result')
CREATE TABLE event_kill ('game', 'round', 'timestamp', 'date', 'killerPlayfabId', 'killerTeam', 'victimPlayfabId', 'victimTeam', 'weaponName')
CREATE TABLE event_cap ('game', 'round', 'mapName', 'timestamp', 'cappingTeam', 'playfabId', 'millisSinceStart')
"""


def import_games(logs_dir, sqlite_path):
    logs = [f for f in listdir(logs_dir) if isfile(join(logs_dir, f))]
    games = []
    for log in logs:
        with open(logs_dir + "/" + log, "r") as f:
            games.append(json.load(f))

    import sqlite3

    if exists(sqlite_path):
        os.remove(sqlite_path)
    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()

    for query in PREPARE_TABLES_QUERIES.strip().split("\n"):
        cur.execute(query)

    supported_playlist_code = ["CTF-Standard-4", "CTF-Standard-6", "CTF-Standard-8"]
    for game in games:
        if game["playlistCode"] not in supported_playlist_code:
            continue
        game["redRoundWins"] = game["teamRoundWins"]["Red"]
        game["blueRoundWins"] = game["teamRoundWins"]["Blue"]
        game["winner"] = game["result"]["winner"]
        game["date"] = datetime.utcfromtimestamp(game["startTime"] / 1000).strftime('%Y-%m-%d')
        cur.execute(
            'insert into game values (:startTime, :date, :playlistCode, :redRoundWins, :blueRoundWins, :winner)', game)
        for round_no, round in enumerate(game["rounds"]):
            row = round
            row["round"] = round_no
            row["date"] = game["date"]
            row["game"] = game["startTime"]
            caps_diff = round["redCaps"] - round["blueCaps"]
            row["result"] = "tie" if caps_diff == 0 else ("redWins" if caps_diff > 0 else "blueWins")
            cur.execute(
                'insert into round values (:game, :date, :round, :mapName, :startTime, :endTime, :blueCaps, :redCaps, :result)',
                row)
            for event in round["events"]:
                row = dict(event)
                del row["type"]
                if event["type"] == "PLAYER_KILL":
                    row["game"] = game["startTime"]
                    row["round"] = round_no
                    row["date"] = datetime.utcfromtimestamp(row["timestamp"] / 1000).strftime('%Y-%m-%d')
                    cur.execute(
                        'insert into event_kill values (:game, :round, :timestamp, :date, :killerPlayfabId, :killerTeam, :victimPlayfabId, :victimTeam, :weaponName)',
                        row)
                elif event["type"] == "FLAG_CAP":
                    row["game"] = game["startTime"]
                    row["mapName"] = round["mapName"]
                    row["round"] = round_no
                    row["millisSinceStart"] = event["timestamp"] - round["startTime"]
                    cur.execute(
                        'insert into event_cap values (:game, :round, :mapName, :timestamp, :cappingTeam, :playfabId, :millisSinceStart)',
                        row)
    con.commit()
    return con, cur
