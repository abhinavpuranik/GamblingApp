from abc import ABC, abstractmethod
from decimal import Decimal
import random
from decimal import Decimal
from abc import ABC, abstractmethod

class BettingStrategy(ABC):
    """Base class — all strategies must implement calculate_bet_amount."""

    @abstractmethod
    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        pass

    @abstractmethod
    def reset(self):
        """Reset internal state back to initial (called after session ends)."""
        pass


# ── 1. Fixed ──────────────────────────────────────────────────────────────────

class FixedAmountStrategy(BettingStrategy):
    """Always bets the same fixed amount regardless of outcome."""

    def __init__(self, fixed_amount: Decimal):
        if fixed_amount <= 0:
            raise ValueError("Fixed amount must be positive")
        self.fixed_amount = fixed_amount

    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        return self.fixed_amount

    def reset(self):
        pass  # stateless — nothing to reset


# ── 2. Percentage ─────────────────────────────────────────────────────────────

class PercentageStrategy(BettingStrategy):
    """Bets a fixed percentage of the current stake each time."""

    def __init__(self, percentage: Decimal):
        if not (Decimal("0") < percentage <= Decimal("100")):
            raise ValueError("Percentage must be between 0 and 100")
        self.percentage = percentage

    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        return round(current_stake * (self.percentage / Decimal("100")), 2)

    def reset(self):
        pass  # stateless


# ── 3. Martingale ─────────────────────────────────────────────────────────────

class MartingaleStrategy(BettingStrategy):
    """
    Double bet after each loss, reset to base amount after a win.
    High risk — can escalate quickly on a losing streak.
    """

    def __init__(self, base_amount: Decimal):
        if base_amount <= 0:
            raise ValueError("Base amount must be positive")
        self.base_amount    = base_amount
        self.current_amount = base_amount

    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        if last_won is None:
            # first bet of session
            self.current_amount = self.base_amount
        elif last_won:
            self.current_amount = self.base_amount          # reset on win
        else:
            self.current_amount = self.current_amount * 2  # double on loss

        return self.current_amount

    def reset(self):
        self.current_amount = self.base_amount


# ── 4. Reverse Martingale ─────────────────────────────────────────────────────

class ReverseMartingaleStrategy(BettingStrategy):
    """
    Double bet after each win, reset to base after a loss.
    Rides winning streaks, cuts losses quickly.
    """

    def __init__(self, base_amount: Decimal):
        if base_amount <= 0:
            raise ValueError("Base amount must be positive")
        self.base_amount    = base_amount
        self.current_amount = base_amount

    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        if last_won is None:
            self.current_amount = self.base_amount
        elif last_won:
            self.current_amount = self.current_amount * 2  # double on win
        else:
            self.current_amount = self.base_amount          # reset on loss

        return self.current_amount

    def reset(self):
        self.current_amount = self.base_amount


# ── 5. Fibonacci ──────────────────────────────────────────────────────────────

class FibonacciStrategy(BettingStrategy):
    """
    Move one step forward in the Fibonacci sequence on a loss,
    two steps back on a win. Base unit scales the sequence.

    Sequence (units): 1, 1, 2, 3, 5, 8, 13, 21 ...
    """

    def __init__(self, base_unit: Decimal):
        if base_unit <= 0:
            raise ValueError("Base unit must be positive")
        self.base_unit = base_unit
        self.sequence  = [Decimal("1"), Decimal("1")]  # grows as needed
        self.index     = 0  # current position in sequence

    def _ensure_length(self, n: int):
        """Extend the Fibonacci sequence up to index n if needed."""
        while len(self.sequence) <= n:
            self.sequence.append(self.sequence[-1] + self.sequence[-2])

    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        if last_won is None:
            self.index = 0
        elif last_won:
            self.index = max(0, self.index - 2)  # step back two on win
        else:
            self.index += 1                       # step forward one on loss

        self._ensure_length(self.index)
        return self.sequence[self.index] * self.base_unit

    def reset(self):
        self.index = 0


# ── 6. D'Alembert ─────────────────────────────────────────────────────────────

class DAlembertStrategy(BettingStrategy):
    """
    Increase bet by one unit after a loss, decrease by one unit after a win.
    Never goes below the base unit.
    Gentler progression than Martingale.
    """

    def __init__(self, base_unit: Decimal):
        if base_unit <= 0:
            raise ValueError("Base unit must be positive")
        self.base_unit      = base_unit
        self.current_amount = base_unit

    def calculate_bet_amount(self, current_stake: Decimal,
                             last_bet: Decimal = None,
                             last_won: bool = None) -> Decimal:
        if last_won is None:
            self.current_amount = self.base_unit
        elif last_won:
            # decrease by one unit, floor at base_unit
            self.current_amount = max(self.base_unit,
                                      self.current_amount - self.base_unit)
        else:
            self.current_amount += self.base_unit  # increase by one unit

        return self.current_amount

    def reset(self):
        self.current_amount = self.base_unit

class OutcomeStrategy(ABC):
    """Determines whether a bet is won or lost."""

    @abstractmethod
    def determine_outcome(self, win_probability: Decimal) -> bool:
        pass


class RandomOutcomeStrategy(OutcomeStrategy):
    """
    Pure random — rolls against win_probability with no adjustment.
    If roll < win_probability → win.
    """
    def determine_outcome(self, win_probability: Decimal) -> bool:
        return Decimal(str(random.random())) < win_probability


class WeightedProbabilityStrategy(OutcomeStrategy):
    """
    Applies a house edge that slightly reduces the effective win probability,
    simulating a realistic casino environment.
    house_edge of 0.03 means the casino keeps 3% long-term.
    """
    def __init__(self, house_edge: Decimal = Decimal("0.03")):
        if not (Decimal("0") <= house_edge < Decimal("1")):
            raise ValueError("house_edge must be between 0 and 1")
        self.house_edge = house_edge

    def determine_outcome(self, win_probability: Decimal) -> bool:
        effective_probability = win_probability * (1 - self.house_edge)
        return Decimal(str(random.random())) < effective_probability