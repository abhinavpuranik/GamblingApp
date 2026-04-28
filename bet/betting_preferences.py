import uuid
from datetime import datetime
from decimal import Decimal
from db import get_connection


class BettingPreferences:
    def __init__(self, gambler_id: str, min_bet: Decimal, max_bet: Decimal,
                 preferred_game_type: str, auto_play_enabled: bool,
                 auto_play_max_games: int, session_loss_limit: Decimal,
                 session_win_target: Decimal):

        if min_bet <= 0:
            raise ValueError("min_bet must be positive")
        if max_bet <= 0:
            raise ValueError("max_bet must be positive")
        if min_bet > max_bet:
            raise ValueError("min_bet cannot exceed max_bet")
        if session_loss_limit <= 0:
            raise ValueError("session_loss_limit must be positive")
        if session_win_target <= 0:
            raise ValueError("session_win_target must be positive")

        self.preference_id      = str(uuid.uuid4())
        self.gambler_id         = gambler_id
        self.min_bet            = min_bet
        self.max_bet            = max_bet
        self.preferred_game_type = preferred_game_type
        self.auto_play_enabled  = auto_play_enabled
        self.auto_play_max_games = auto_play_max_games
        self.session_loss_limit = session_loss_limit
        self.session_win_target = session_win_target
        self.updated_at         = datetime.now()

    # ── persistence ────────────────────────────────────────────────────────────

    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO BETTING_PREFERENCES (
                    preference_id, gambler_id, min_bet, max_bet,
                    preferred_game_type, auto_play_enabled, auto_play_max_games,
                    session_loss_limit, session_win_target, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.preference_id, self.gambler_id, self.min_bet, self.max_bet,
                  self.preferred_game_type, self.auto_play_enabled,
                  self.auto_play_max_games, self.session_loss_limit,
                  self.session_win_target, self.updated_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update(self):
        """Persists all preference fields."""
        self.updated_at = datetime.now()
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE BETTING_PREFERENCES
                SET min_bet = %s, max_bet = %s, preferred_game_type = %s,
                    auto_play_enabled = %s, auto_play_max_games = %s,
                    session_loss_limit = %s, session_win_target = %s,
                    updated_at = %s
                WHERE preference_id = %s
            """, (self.min_bet, self.max_bet, self.preferred_game_type,
                  self.auto_play_enabled, self.auto_play_max_games,
                  self.session_loss_limit, self.session_win_target,
                  self.updated_at, self.preference_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    # ── queries ────────────────────────────────────────────────────────────────

    @staticmethod
    def find_by_gambler(gambler_id: str):
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM BETTING_PREFERENCES WHERE gambler_id = %s", (gambler_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()