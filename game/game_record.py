import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from db import get_connection


class GameOutcome(Enum):
    WIN  = "WIN"
    LOSS = "LOSS"


class GameRecord:
    def __init__(self, session_id: str, bet_id: str, odds_config_id: str,
                 outcome: GameOutcome, bet_amount: Decimal,
                 payout_amount: Decimal, loss_amount: Decimal,
                 stake_before: Decimal, stake_after: Decimal,
                 consecutive_win_streak: int, consecutive_loss_streak: int,
                 game_duration_ms: int):

        if not isinstance(outcome, GameOutcome):
            raise ValueError("outcome must be a GameOutcome enum value")
        if bet_amount <= 0:
            raise ValueError("bet_amount must be positive")
        if stake_before < 0 or stake_after < 0:
            raise ValueError("Stakes cannot be negative")

        self.game_id                 = str(uuid.uuid4())
        self.session_id              = session_id
        self.bet_id                  = bet_id
        self.odds_config_id          = odds_config_id
        self.outcome                 = outcome
        self.bet_amount              = bet_amount
        self.payout_amount           = payout_amount
        self.loss_amount             = loss_amount
        self.net_change              = payout_amount - loss_amount
        self.stake_before            = stake_before
        self.stake_after             = stake_after
        self.consecutive_win_streak  = consecutive_win_streak
        self.consecutive_loss_streak = consecutive_loss_streak
        self.game_duration_ms        = game_duration_ms
        self.resolved_at             = datetime.now()

    

    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO GAME_RECORDS (game_id, session_id, bet_id, odds_config_id,
                    outcome, bet_amount, payout_amount, loss_amount, net_change,
                    stake_before, stake_after, consecutive_win_streak,
                    consecutive_loss_streak, game_duration_ms, resolved_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.game_id, self.session_id, self.bet_id, self.odds_config_id,
                  self.outcome.value,
                  self.bet_amount, self.payout_amount,
                  self.loss_amount, self.net_change,
                  self.stake_before, self.stake_after,
                  self.consecutive_win_streak, self.consecutive_loss_streak,
                  self.game_duration_ms, self.resolved_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def from_bet(bet, session_id: str, odds_config_id: str,
                 consecutive_win_streak: int, consecutive_loss_streak: int,
                 game_duration_ms: int) -> "GameRecord":
        if not bet.is_settled:
            raise Exception("Bet must be settled before creating GameRecord")

        outcome       = GameOutcome.WIN  if bet.won else GameOutcome.LOSS
        payout_amount = bet.potential_win if bet.won else Decimal("0.00")
        loss_amount   = Decimal("0.00")  if bet.won else bet.bet_amount

        return GameRecord(
            session_id=session_id,
            bet_id=bet.bet_id,
            odds_config_id=odds_config_id,
            outcome=outcome,
            bet_amount=bet.bet_amount,
            payout_amount=payout_amount,
            loss_amount=loss_amount,
            stake_before=bet.stake_before,
            stake_after=bet.stake_after,
            consecutive_win_streak=consecutive_win_streak,
            consecutive_loss_streak=consecutive_loss_streak,
            game_duration_ms=game_duration_ms
        )

    @staticmethod
    def find_by_bet(bet_id: str):
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM GAME_RECORDS WHERE bet_id = %s", (bet_id,))
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
                SELECT * FROM GAME_RECORDS
                WHERE session_id = %s
                ORDER BY resolved_at ASC
            """, (session_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_wins_by_session(session_id: str) -> list:
        conn   = get_connection()          
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM GAME_RECORDS
                WHERE session_id = %s AND outcome = 'WIN'
                ORDER BY resolved_at ASC
            """, (session_id,))           
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_losses_by_session(session_id: str) -> list:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM GAME_RECORDS
                WHERE session_id = %s AND outcome = 'LOSS'
                ORDER BY resolved_at ASC
            """, (session_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()