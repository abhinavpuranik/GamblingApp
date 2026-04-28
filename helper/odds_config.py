from decimal import Decimal
from enum import Enum


class OddsType(Enum):
    FIXED             = "FIXED"
    PROBABILITY_BASED = "PROBABILITY_BASED"
    AMERICAN          = "AMERICAN"
    DECIMAL           = "DECIMAL"


class OddsConfiguration:
    """
    Calculates potential winnings based on odds type and format.
    All calculate() methods return the PROFIT only (not including stake back).
    The full payout (profit + stake) is handled in Bet.settle().
    """

    def __init__(self, odds_type: OddsType, odds_value: Decimal):
        self.odds_type  = odds_type
        self.odds_value = odds_value

    def calculate_potential_win(self, bet_amount: Decimal) -> Decimal:
        """
        Routes to the correct calculation based on odds_type.
        Returns total payout (stake + profit) to match how Bet stores potential_win.
        """
        if self.odds_type == OddsType.FIXED:
            return self._fixed(bet_amount)
        elif self.odds_type == OddsType.PROBABILITY_BASED:
            return self._probability_based(bet_amount)
        elif self.odds_type == OddsType.AMERICAN:
            return self._american(bet_amount)
        elif self.odds_type == OddsType.DECIMAL:
            return self._decimal(bet_amount)
        else:
            raise ValueError(f"Unknown odds type: {self.odds_type}")

    def _fixed(self, bet_amount: Decimal) -> Decimal:
        """
        Simple multiplier. odds_value of 1.90 means
        you get back $1.90 per $1 bet (profit = $0.90).
        """
        return round(bet_amount * self.odds_value, 2)

    def _probability_based(self, bet_amount: Decimal) -> Decimal:
        """
        Lower probability → higher payout.
        potential_win = bet_amount / win_probability.
        odds_value here is the win_probability (e.g. 0.45).
        """
        if self.odds_value <= 0:
            raise ValueError("Probability must be positive")
        return round(bet_amount / self.odds_value, 2)

    def _american(self, bet_amount: Decimal) -> Decimal:
        """
        Positive odds (underdog): odds_value = +150 means
        $100 bet wins $150 profit → payout = bet + profit.
        Negative odds (favorite): odds_value = -110 means
        you must bet $110 to win $100 profit.
        """
        if self.odds_value > 0:
            profit = bet_amount * (self.odds_value / Decimal("100"))
        else:
            profit = bet_amount * (Decimal("100") / abs(self.odds_value))
        return round(bet_amount + profit, 2)

    def _decimal(self, bet_amount: Decimal) -> Decimal:
        """
        European format. odds_value of 2.10 means
        total payout = bet_amount * 2.10 (profit = bet * 1.10).
        """
        return round(bet_amount * self.odds_value, 2)

    def describe(self) -> str:
        return f"{self.odds_type.value} @ {self.odds_value}"