import uuid
from datetime import datetime
from decimal import Decimal
from db import get_connection
from helper.transaction_type import TransactionType


class StakeTransaction:
    def __init__(self, gambler_id: str, session_id: str,
                 transaction_type: TransactionType,
                 amount: Decimal, balance_before: Decimal,
                 balance_after: Decimal, bet_id: str = None,
                 notes: str = None):

        if amount <= 0:
            raise ValueError("Transaction amount must be positive")

        self.transaction_id   = str(uuid.uuid4())
        self.gambler_id       = gambler_id
        self.session_id       = session_id
        self.transaction_type = transaction_type
        self.amount           = amount
        self.balance_before   = balance_before
        self.balance_after    = balance_after
        self.net_change       = balance_after - balance_before
        self.bet_id           = bet_id        # nullable — only set for BET_* types
        self.notes            = notes
        self.created_at       = datetime.now()

    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO STAKE_TRANSACTIONS (
                    transaction_id, gambler_id, session_id, transaction_type,
                    amount, balance_before, balance_after, net_change,
                    bet_id, notes, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.transaction_id, self.gambler_id, self.session_id,
                  self.transaction_type.value, self.amount,
                  self.balance_before, self.balance_after, self.net_change,
                  self.bet_id, self.notes, self.created_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_session(session_id: str) -> list:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM STAKE_TRANSACTIONS
                WHERE session_id = %s
                ORDER BY created_at ASC
            """, (session_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_gambler(gambler_id: str) -> list:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM STAKE_TRANSACTIONS
                WHERE gambler_id = %s
                ORDER BY created_at ASC
            """, (gambler_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_type(session_id: str, transaction_type: TransactionType) -> list:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM STAKE_TRANSACTIONS
                WHERE session_id = %s AND transaction_type = %s
                ORDER BY created_at ASC
            """, (session_id, transaction_type.value))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_bet(bet_id: str) -> list:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM STAKE_TRANSACTIONS
                WHERE bet_id = %s
                ORDER BY created_at ASC
            """, (bet_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()