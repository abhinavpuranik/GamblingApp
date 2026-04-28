from decimal import Decimal
from datetime import datetime


class StakeMonitor:
    """
    In-memory real-time tracker for a single session.
    Does NOT write to the DB — StakeTransaction handles persistence.
    """

    def __init__(self, session_id: str, initial_stake: Decimal):
        self.session_id    = session_id
        self.initial_stake = initial_stake
        self.current_stake = initial_stake
        self.peak_stake    = initial_stake
        self.lowest_stake  = initial_stake
        self.started_at    = datetime.now()

    
        self.stake_history: list = [
            {"stake": initial_stake, "timestamp": self.started_at, "event": "SESSION_START"}
        ]

    def record_change(self, new_stake: Decimal, event: str):
        """Call this after every stake update."""
        self.current_stake = new_stake
        self.peak_stake    = max(self.peak_stake,   new_stake)
        self.lowest_stake  = min(self.lowest_stake, new_stake)
        self.stake_history.append({
            "stake":     new_stake,
            "timestamp": datetime.now(),
            "event":     event
        })

    def get_fluctuation_analysis(self) -> dict:
        """
        Returns peak, lowest, net change, volatility, and total moves.
        Volatility = average absolute change between consecutive readings.
        """
        net_change = self.current_stake - self.initial_stake

        if len(self.stake_history) < 2:
            volatility    = Decimal("0.00")
            total_changes = 0
        else:
            deltas = [
                abs(self.stake_history[i]["stake"] - self.stake_history[i-1]["stake"])
                for i in range(1, len(self.stake_history))
            ]
            volatility    = round(sum(deltas) / len(deltas), 2)
            total_changes = len(deltas)

        return {
            "session_id":    self.session_id,
            "initial_stake": self.initial_stake,
            "current_stake": self.current_stake,
            "peak_stake":    self.peak_stake,
            "lowest_stake":  self.lowest_stake,
            "net_change":    net_change,
            "volatility":    volatility,
            "total_changes": total_changes,
            "duration_mins": round(
                (datetime.now() - self.started_at).total_seconds() / 60, 2)
        }