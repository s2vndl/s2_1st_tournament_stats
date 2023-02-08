import os
import sqlite3
import tempfile
import uuid
from os.path import exists
from typing import List, Union

import atexit

from s2_analytics.importer import GameDetails, GameProcessor, RoundData, EventKill, EventFlagCap, EventProcessor, \
    RoundProcessor, EventData


class SqliteCollector(GameProcessor, RoundProcessor, EventProcessor):
    def __init__(self, sqlite_path: Union[None, str] = None, sqlite_conn: Union[sqlite3.Connection, None] = None):
        self.games: List[GameDetails] = []
        self.rounds: List[RoundData] = []
        self.events: List[EventData] = []
        self.sqlite_path = sqlite_path
        self.connection: Union[sqlite3.Connection, None] = sqlite_conn
        self.cursor: Union[sqlite3.Cursor, None] = None
        self.round_id = 0

    def init(self) -> "SqliteCollector":
        if self.connection is None:
            self.connection = self._prepare_sqlite_db(self.sqlite_path)
        self.cursor = self.connection.cursor()
        self._create_tables()
        return self

    def _create_tables(self):
        queries = """
            CREATE TABLE game ('id', 'date', playlistCode'', 'redRoundWins', 'blueRoundWins', 'winner')
            CREATE TABLE round ('id', 'game', 'date', 'round', 'mapName', 'startTime', 'endTime', 'blueCaps', 'redCaps', 'result')
            CREATE TABLE event_kill ('game', 'round', 'timestamp', 'date', 'killerPlayfabId', 'killerTeam', 'victimPlayfabId', 'victimTeam', 'weaponName')
            CREATE TABLE event_cap ('game', 'round', 'mapName', 'timestamp', 'cappingTeam', 'playfabId', 'millisSinceStart')
        """
        for query in queries.strip().split("\n"):
            self.cursor.execute(query)

    def _prepare_sqlite_db(self, sqlite_path: Union[None, str]):
        if sqlite_path is None:
            sqlite_path = tempfile.gettempdir() + f"/s2_analytics_{uuid.uuid4()}.sqlite"
        if exists(sqlite_path):
            os.remove(sqlite_path)
        con = sqlite3.connect(sqlite_path)
        self._register_cleanup(sqlite_path)
        return con

    def _register_cleanup(self, sqlite_path: str):
        def delete_if_exists(path):
            if exists(path):
                os.remove(path)

        atexit.register(delete_if_exists, sqlite_path)

    def process_game(self, game: GameDetails):
        self.cursor.execute("""
                insert into game 
                    values (:startTime, :date, :playlistCode, :scoreRed, :scoreBlue, :winner)
            """, {"startTime": game.id, "date": game.date_iso, "playlistCode": game.playlist_code,
                  "scoreRed": game.score_red, "scoreBlue": game.score_blue, "winner": game.winner})

    def process_round(self, round: RoundData, game: GameDetails):
        self.round_id += 1
        self.cursor.execute("""
                insert into round 
                    values (:id, :game, :date, :round, :mapName, :startTime, 
                        :endTime, :blueCaps, :redCaps, :winner) 
            """, {"id": self.round_id, "game": game.id, "date": round.date_iso, "round": round.number,
                  "mapName": round.map, "startTime": round.start_time, "endTime": round.end_time,
                  "blueCaps": round.score_blue, "redCaps": round.score_red,
                  "winner": round.winner})

    def process_event(self, event: EventData, round: RoundData, game: GameDetails):
        if isinstance(event, EventKill):
            self.cursor.execute("""
                insert into event_kill 
                    values (:game, :round, :timestamp, :date, :killer, 
                        :killerTeam, :victim, :victimTeam, :weapon)""",
                                {
                                    "game": game.id, "round": round.game_id, "timestamp": event.timestamp,
                                    "date": event.date_iso, "killer": event.killer_id, "killerTeam": event.killer_team,
                                    "victim": event.victim_id, "victimTeam": event.victim_team,
                                    "weapon": event.weapon
                                })
        elif isinstance(event, EventFlagCap):
            self.cursor.execute("""
            insert into event_cap 
                        values (:game, :round, :map, :timestamp,
                            :team, :player, :millisSinceStart)""",
                                {
                                    "game": game.id, "round": round.game_id, "map":round.map, "timestamp": event.timestamp,
                                    "date": event.date_iso, "team": event.capping_team,
                                    "player": event.capping_player_id,
                                    "millisSinceStart": (event.timestamp.timestamp()-round.start_time.timestamp())*1000
                                })

    def finalize_game_processing(self):
        self.cursor.close()
        self.connection.commit()

