import uuid
import random
from datetime import datetime
from decimal import Decimal
from db import get_connection


class Bet:
    def __init__(self, session_id: str, gambler_id: str, strategy_id: int,
                 game_index: int, bet_amount: Decimal, win_probability: Decimal,
                 odds_type: str, odds_value: Decimal, stake_before: Decimal):

        if bet_amount <= 0:
            raise ValueError("Bet amount must be positive")
        if not (Decimal("0") < win_probability <= Decimal("1")):
            raise ValueError("Win probability must be between 0 and 1")
        if bet_amount > stake_before:
            raise ValueError(
                f"Bet amount ${bet_amount} exceeds available stake ${stake_before}")

        self.bet_id          = str(uuid.uuid4())
        self.session_id      = session_id
        self.gambler_id      = gambler_id
        self.strategy_id     = strategy_id
        self.game_index      = game_index
        self.bet_amount      = bet_amount
        self.win_probability = win_probability
        self.odds_type       = odds_type
        self.odds_value      = odds_value
        self.potential_win   = round(bet_amount * odds_value, 2)
        self.stake_before    = stake_before
        self.stake_after     = None
        self.is_settled      = False
        self.won             = None     # True/False after settlement
        self.placed_at       = datetime.now()

    def determine_outcome(self) -> bool:
        """
        Simulates a bet outcome using the configured win probability.
        Returns True if the bet is won, False otherwise.
        random.random() produces a float in [0.0, 1.0).
        If it falls below win_probability the bet is a win.
        """
        roll = Decimal(str(random.random()))
        self.won = roll < self.win_probability
        return self.won

    def settle(self, stake_before_settlement: Decimal) -> Decimal:
        """
        Calculates stake_after based on outcome.
        Must call determine_outcome() before settle().
        Returns the new stake.
        """
        if self.won is None:
            raise Exception("Call determine_outcome() before settle()")

        if self.won:
            # stake back + winnings (potential_win already includes the bet amount)
            self.stake_after = stake_before_settlement + self.potential_win
        else:
            # stake was already reserved — nothing comes back
            self.stake_after = stake_before_settlement

        self.is_settled = True
        return self.stake_after

    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO BETS (bet_id, session_id, gambler_id, strategy_id,
                    game_index, bet_amount, win_probability, odds_type, odds_value,
                    potential_win, stake_before, stake_after, is_settled, placed_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.bet_id, self.session_id, self.gambler_id, self.strategy_id,
                  self.game_index, self.bet_amount, self.win_probability,
                  self.odds_type, self.odds_value, self.potential_win,
                  self.stake_before, self.stake_after, self.is_settled,
                  self.placed_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_settlement(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE BETS SET stake_after = %s, is_settled = %s
                WHERE bet_id = %s
            """, (self.stake_after, self.is_settled, self.bet_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_id(bet_id: str):
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM BETS WHERE bet_id = %s", (bet_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_session(session_id: str) -> list:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM BETS WHERE session_id = %s ORDER BY placed_at ASC
            """, (session_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()