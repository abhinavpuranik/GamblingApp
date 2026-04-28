import uuid
from datetime import datetime
from decimal import Decimal
from db import get_connection
from validation.validation import InputValidator, ValidationConfig


class GamblingProfile:
    def __init__(self, username: str, full_name: str, email: str,
                 initial_stake: Decimal, win_threshold: Decimal,
                 loss_threshold: Decimal, min_required_stake: Decimal):
        
        validator = InputValidator(ValidationConfig())
        res = validator.validate_initial_stake(initial_stake)

        if not res.is_valid:
            raise ValueError(res.errors)

        if initial_stake < min_required_stake:
            raise ValueError("Initial stake must be >= minimum required stake")
        if win_threshold <= initial_stake:
            raise ValueError("Win threshold must be greater than initial stake")
        if loss_threshold >= initial_stake:
            raise ValueError("Loss threshold must be less than initial stake")
        if loss_threshold < min_required_stake:
            raise ValueError("Loss threshold cannot be below minimum required stake")

        self.gambler_id         = str(uuid.uuid4())
        self.username           = username
        self.full_name          = full_name
        self.email              = email
        self.is_active          = True
        self.initial_stake      = initial_stake
        self.current_stake      = initial_stake
        self.win_threshold      = win_threshold
        self.loss_threshold     = loss_threshold
        self.min_required_stake = min_required_stake
        self.total_bets         = 0
        self.total_wins         = 0
        self.total_losses       = 0
        self.total_winnings     = Decimal("0.00")
        self.created_at         = datetime.now()
        self.updated_at         = datetime.now()



    def record_win(self, amount: Decimal):
        if not self.is_active:
            raise Exception("Gambler account is inactive")
        if amount <= 0:
            raise ValueError("Win amount must be positive")
        self.current_stake  += amount
        self.total_bets     += 1
        self.total_wins     += 1
        self.total_winnings += amount
        self.updated_at      = datetime.now()

    def record_loss(self, amount: Decimal):
        if not self.is_active:
            raise Exception("Gambler account is inactive")
        if amount <= 0:
            raise ValueError("Loss amount must be positive")
        if amount > self.current_stake:
            raise ValueError("Insufficient balance")
        self.current_stake  -= amount
        self.total_bets     += 1
        self.total_losses   += 1
        self.updated_at      = datetime.now()

    def deactivate(self):
        self.is_active  = False
        self.updated_at = datetime.now()

    

    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO GAMBLERS (
                    gambler_id, username, full_name, email, is_active,
                    initial_stake, current_stake, win_threshold, loss_threshold,
                    min_required_stake, total_bets, total_wins, total_losses,
                    total_winnings, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.gambler_id, self.username, self.full_name, self.email,
                  self.is_active, self.initial_stake, self.current_stake,
                  self.win_threshold, self.loss_threshold, self.min_required_stake,
                  self.total_bets, self.total_wins, self.total_losses,
                  self.total_winnings, self.created_at, self.updated_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_stake_and_stats(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE GAMBLERS
                SET current_stake = %s, total_bets = %s, total_wins = %s,
                    total_losses = %s, total_winnings = %s, updated_at = %s
                WHERE gambler_id = %s
            """, (self.current_stake, self.total_bets, self.total_wins,
                  self.total_losses, self.total_winnings,
                  self.updated_at, self.gambler_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_personal_info(self):
        """Persists username, full_name, email changes."""
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE GAMBLERS
                SET username = %s, full_name = %s, email = %s, updated_at = %s
                WHERE gambler_id = %s
            """, (self.username, self.full_name, self.email,
                  self.updated_at, self.gambler_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_thresholds(self):
        """Persists win_threshold and loss_threshold changes."""
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE GAMBLERS
                SET win_threshold = %s, loss_threshold = %s, updated_at = %s
                WHERE gambler_id = %s
            """, (self.win_threshold, self.loss_threshold,
                  self.updated_at, self.gambler_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_status(self):
        """Persists is_active flag."""
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE GAMBLERS SET is_active = %s, updated_at = %s
                WHERE gambler_id = %s
            """, (self.is_active, self.updated_at, self.gambler_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def reset_to_initial(self):
        """Resets financial + stat fields for a fresh session. Persists everything."""
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE GAMBLERS
                SET current_stake = %s, total_bets = %s, total_wins = %s,
                    total_losses = %s, total_winnings = %s,
                    win_threshold = %s, loss_threshold = %s,
                    is_active = %s, updated_at = %s
                WHERE gambler_id = %s
            """, (self.current_stake, self.total_bets, self.total_wins,
                  self.total_losses, self.total_winnings,
                  self.win_threshold, self.loss_threshold,
                  self.is_active, self.updated_at, self.gambler_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def find_by_id(gambler_id: str):
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_username(username: str):
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM GAMBLERS WHERE username = %s", (username,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()