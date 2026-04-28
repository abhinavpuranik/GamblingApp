from enum import Enum
from decimal import Decimal
from decimal import Decimal, InvalidOperation
import math

class ValidationErrorType(Enum):
    STAKE_ERROR       = "STAKE_ERROR"
    BET_ERROR         = "BET_ERROR"
    LIMIT_ERROR       = "LIMIT_ERROR"
    PROBABILITY_ERROR = "PROBABILITY_ERROR"
    NUMERIC_ERROR     = "NUMERIC_ERROR"
    RANGE_ERROR       = "RANGE_ERROR"
    NULL_ERROR        = "NULL_ERROR"

class ValidationException(Exception):
    def __init__(self, message, error_type, field=None, value=None):
        super().__init__(message)
        self.error_type = error_type
        self.field = field
        self.value = value


class StakeValidationException(ValidationException):
    pass

class BetValidationException(ValidationException):
    pass

class LimitValidationException(ValidationException):
    pass

class ProbabilityValidationException(ValidationException):
    pass

class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, message):
        self.errors.append(message)

    def add_warning(self, message):
        self.warnings.append(message)

    @property
    def is_valid(self):
        return len(self.errors) == 0

    def summary(self):
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
class ValidationConfig:
    def __init__(
        self,
        min_stake=Decimal("0.00"),
        max_stake=Decimal("1000000.00"),
        min_bet=Decimal("1.00"),
        max_bet=Decimal("10000.00"),
        min_probability=Decimal("0.0"),
        max_probability=Decimal("1.0"),
        allow_zero_stake=False,
        strict_mode=True
    ):
        self.min_stake = min_stake
        self.max_stake = max_stake
        self.min_bet = min_bet
        self.max_bet = max_bet
        self.min_probability = min_probability
        self.max_probability = max_probability
        self.allow_zero_stake = allow_zero_stake
        self.strict_mode = strict_mode

class InputValidator:

    def __init__(self, config: ValidationConfig):
        self.config = config

    # ✅ 1. Initial Stake
    def validate_initial_stake(self, stake: Decimal) -> ValidationResult:
        result = ValidationResult()

        if stake is None:
            result.add_error("Stake cannot be null")
            return result

        if stake < 0:
            result.add_error("Stake cannot be negative")

        if stake == 0 and not self.config.allow_zero_stake:
            result.add_error("Zero stake not allowed")

        if stake < self.config.min_stake:
            result.add_error(f"Stake below minimum {self.config.min_stake}")

        if stake > self.config.max_stake:
            result.add_error(f"Stake exceeds max {self.config.max_stake}")

        return result

    # ✅ 2. Bet validation
    def validate_bet_amount(self, bet, current_stake):
        result = ValidationResult()

        if bet <= 0:
            result.add_error("Bet must be positive")

        if bet > current_stake:
            result.add_error("Bet exceeds current stake")

        if bet < self.config.min_bet:
            result.add_error("Bet below minimum")

        if bet > self.config.max_bet:
            result.add_error("Bet above maximum")

        return result

    # ✅ 3. Limits
    def validate_limits(self, lower, upper, initial_stake=None):
        result = ValidationResult()

        if lower < 0 or upper < 0:
            result.add_error("Limits cannot be negative")

        if upper <= lower:
            result.add_error("Upper limit must be greater than lower")

        if initial_stake and not (lower <= initial_stake <= upper):
            result.add_warning("Initial stake not within limits")

        return result

    # ✅ 4. Numeric parsing
    def parse_and_validate_numeric(self, value_str):
        result = ValidationResult()

        try:
            value = Decimal(value_str)

            if math.isinf(float(value)) or math.isnan(float(value)):
                result.add_error("Invalid number (NaN or Infinity)")
                return None, result

            return value, result

        except (InvalidOperation, ValueError):
            result.add_error(f"Invalid numeric input: {value_str}")
            return None, result

    # ✅ 5. Non-negative stake
    def validate_stake_non_negative(self, stake):
        result = ValidationResult()

        if stake < 0:
            result.add_error("Stake cannot go negative")

        return result

    # ✅ 6. Probability
    def validate_probability(self, prob):
        result = ValidationResult()

        if prob < self.config.min_probability or prob > self.config.max_probability:
            result.add_error("Probability must be between 0 and 1")

        return result