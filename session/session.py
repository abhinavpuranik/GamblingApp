import uuid
from datetime import datetime
from decimal import Decimal
from db import get_connection

class Session:
    def __init__(self, gambler_id: str, starting_stake: Decimal, max_games: int):
        self.session_id = str(uuid.uuid4())
        self.gambler_id = gambler_id
        self.status = "ACTIVE"
        self.end_reason = None
        self.starting_stake = starting_stake
        self.ending_stake = None
        self.peak_stake = starting_stake
        self.lowest_stake = starting_stake
        self.max_games = max_games
        self.games_played = 0
        self.total_pause_seconds = 0
        self.started_at = datetime.now()
        self.ended_at = None
        self.created_at = datetime.now()

    def end(self, end_reason: str, ending_stake: Decimal):
        self.status = "ENDED"
        self.end_reason = end_reason
        self.ending_stake = ending_stake
        self.ended_at = datetime.now()

    def save(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO SESSIONS (session_id, gambler_id, status, end_reason,
                    starting_stake, ending_stake, peak_stake, lowest_stake,
                    max_games, games_played, total_pause_seconds,
                    started_at, ended_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.session_id, self.gambler_id, self.status, self.end_reason,
                  self.starting_stake, self.ending_stake, self.peak_stake, self.lowest_stake,
                  self.max_games, self.games_played, self.total_pause_seconds,
                  self.started_at, self.ended_at, self.created_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_status(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE SESSIONS SET status = %s, end_reason = %s, ending_stake = %s,
                    ended_at = %s WHERE session_id = %s
            """, (self.status, self.end_reason, self.ending_stake,
                  self.ended_at, self.session_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_id(session_id: str):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM SESSIONS WHERE session_id = %s", (session_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_gambler(gambler_id: str):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM SESSIONS WHERE gambler_id = %s", (gambler_id,))
            return cursor.fetchall()  # one-to-many: list of all sessions for this gambler
        finally:
            cursor.close()
            conn.close()