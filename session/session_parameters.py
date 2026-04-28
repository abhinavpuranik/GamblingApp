import uuid
from datetime import datetime
from decimal import Decimal
from db import get_connection
from validation.validation import InputValidator, ValidationConfig

validator = InputValidator(ValidationConfig())
class SessionParameters:
    def __init__(self, session_id: str,
                 lower_limit: Decimal, upper_limit: Decimal,
                 min_bet: Decimal, max_bet: Decimal,
                 default_win_probability: Decimal,
                 max_session_minutes: int,
                 maximum_games: int,
                 strict_mode: bool):

      

        if lower_limit < 0:
            raise ValueError(
                f"lower_limit must be >= 0, got {lower_limit}")
        if upper_limit <= lower_limit:
            raise ValueError(
                f"upper_limit ({upper_limit}) must be greater than "
                f"lower_limit ({lower_limit})")

        if min_bet <= 0:
            raise ValueError(
                f"min_bet must be positive, got {min_bet}")
        if max_bet <= 0:
            raise ValueError(
                f"max_bet must be positive, got {max_bet}")
        if min_bet > max_bet:
            raise ValueError(
                f"min_bet ({min_bet}) cannot exceed max_bet ({max_bet})")

        if not (Decimal("0") < default_win_probability <= Decimal("1")):
            raise ValueError(
                f"default_win_probability must be between 0 and 1, "
                f"got {default_win_probability}")

        if max_session_minutes <= 0:
            raise ValueError(
                f"max_session_minutes must be positive, got {max_session_minutes}")
        if maximum_games <= 0:
            raise ValueError(
                f"maximum_games must be positive, got {maximum_games}")

      

        self.parameter_id            = str(uuid.uuid4())
        self.session_id              = session_id
        self.lower_limit             = lower_limit
        self.upper_limit             = upper_limit
        self.min_bet                 = min_bet
        self.max_bet                 = max_bet
        self.default_win_probability = default_win_probability
        self.max_session_minutes     = max_session_minutes
        self.maximum_games           = maximum_games
        self.strict_mode             = strict_mode
        self.created_at              = datetime.now()

    

    def validate_stake(self, current_stake: Decimal) -> dict:
        """
        Checks whether a given stake is within the configured boundaries.
        Used by SessionManagementService to decide if a session should end.
        """
        errors   = []
        warnings = []

        if current_stake <= self.lower_limit:
            errors.append(
                f"Stake ${current_stake} has hit or breached "
                f"lower limit ${self.lower_limit}")
        elif current_stake < self.lower_limit * Decimal("1.10"):
            warnings.append(
                f"Stake ${current_stake} is within 10% of "
                f"lower limit ${self.lower_limit}")

        if current_stake >= self.upper_limit:
            errors.append(
                f"Stake ${current_stake} has hit or exceeded "
                f"upper limit ${self.upper_limit}")
        elif current_stake > self.upper_limit * Decimal("0.90"):
            warnings.append(
                f"Stake ${current_stake} is within 10% of "
                f"upper limit ${self.upper_limit}")

        return {
            "is_valid": len(errors) == 0,
            "errors":   errors,
            "warnings": warnings
        }

    def validate_bet(self, bet_amount: Decimal) -> dict:
        """Checks a proposed bet amount against min/max limits."""
        errors = []
        if bet_amount < self.min_bet:
            errors.append(
                f"Bet ${bet_amount} is below minimum ${self.min_bet}")
        if bet_amount > self.max_bet:
            errors.append(
                f"Bet ${bet_amount} exceeds maximum ${self.max_bet}")
        return {"is_valid": len(errors) == 0, "errors": errors}

    def is_time_exceeded(self, session_started_at: datetime) -> bool:
        elapsed_minutes = (datetime.now() - session_started_at).total_seconds() / 60
        return elapsed_minutes >= self.max_session_minutes

    def is_game_limit_reached(self, games_played: int) -> bool:
        return games_played >= self.maximum_games



    def save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO SESSION_PARAMETERS (
                    parameter_id, session_id, lower_limit, upper_limit,
                    min_bet, max_bet, default_win_probability,
                    max_session_minutes, maximum_games, strict_mode, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.parameter_id, self.session_id,
                  self.lower_limit, self.upper_limit,
                  self.min_bet, self.max_bet,
                  self.default_win_probability, self.max_session_minutes,
                  self.maximum_games, self.strict_mode, self.created_at))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def find_by_session(session_id: str):
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM SESSION_PARAMETERS WHERE session_id = %s",
                (session_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()