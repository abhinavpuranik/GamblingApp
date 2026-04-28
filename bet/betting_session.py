from decimal import Decimal
from datetime import datetime


class BettingSession:
    """
    In-memory session tracker for a single gaming session.
    Stores all Bet objects placed this session and computes summary stats.
    Does NOT write to DB — Session entity handles persistence.
    """

    def __init__(self, session_id: str, gambler_id: str,
                 starting_stake: Decimal):
        self.session_id     = session_id
        self.gambler_id     = gambler_id
        self.starting_stake = starting_stake
        self.current_stake  = starting_stake
        self.bets           = []          # list of Bet objects
        self.started_at     = datetime.now()
        self.ended_at       = None

    def add_bet(self, bet):
        """Append a settled Bet object and update current_stake."""
        self.bets.append(bet)
        if bet.stake_after is not None:
            self.current_stake = bet.stake_after

    def end(self):
        self.ended_at = datetime.now()

    def get_summary(self) -> dict:
        total_bets   = len(self.bets)
        wins         = [b for b in self.bets if b.won]
        losses       = [b for b in self.bets if not b.won]
        total_wagered = sum(b.bet_amount  for b in self.bets)
        total_won     = sum(b.potential_win for b in wins)
        net_change    = self.current_stake - self.starting_stake

        win_rate = (
            round(Decimal(len(wins)) / Decimal(total_bets) * 100, 2)
            if total_bets > 0 else Decimal("0.00")
        )
        avg_bet = (
            round(total_wagered / Decimal(total_bets), 2)
            if total_bets > 0 else Decimal("0.00")
        )

        duration_secs = (
            (self.ended_at - self.started_at).total_seconds()
            if self.ended_at else
            (datetime.now() - self.started_at).total_seconds()
        )

        return {
            "session_id":     self.session_id,
            "gambler_id":     self.gambler_id,
            "starting_stake": self.starting_stake,
            "ending_stake":   self.current_stake,
            "net_change":     net_change,
            "total_bets":     total_bets,
            "total_wins":     len(wins),
            "total_losses":   len(losses),
            "win_rate":       win_rate,
            "total_wagered":  total_wagered,
            "total_won":      total_won,
            "avg_bet":        avg_bet,
            "duration_secs":  round(duration_secs, 2),
        }

    def print_summary(self):
        s = self.get_summary()
        pnl_sign = "+" if s["net_change"] >= 0 else ""
        print(f"\n{'='*52}")
        print(f"  BETTING SESSION SUMMARY")
        print(f"  Session   : {s['session_id']}")
        print(f"{'='*52}")
        print(f"  Starting Stake : ${s['starting_stake']:,.2f}")
        print(f"  Ending Stake   : ${s['ending_stake']:,.2f}")
        print(f"  Net P&L        : {pnl_sign}${s['net_change']:,.2f}")
        print(f"  --")
        print(f"  Total Bets     : {s['total_bets']}")
        print(f"  Wins / Losses  : {s['total_wins']} / {s['total_losses']}")
        print(f"  Win Rate       : {s['win_rate']}%")
        print(f"  Total Wagered  : ${s['total_wagered']:,.2f}")
        print(f"  Total Won      : ${s['total_won']:,.2f}")
        print(f"  Avg Bet        : ${s['avg_bet']:,.2f}")
        print(f"  Duration       : {s['duration_secs']}s")
        print(f"{'='*52}")