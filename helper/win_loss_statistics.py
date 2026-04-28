from decimal import Decimal


class RunningTotals:
    """
    Updated after every game. Tracks cumulative balance and P&L progression.
    Stored inside WinLossStatistics — not a standalone object.
    """

    def __init__(self, starting_balance: Decimal):
        self.starting_balance  = starting_balance
        self.current_balance   = starting_balance
        # each entry: {"game": int, "balance": Decimal, "net_pnl": Decimal}
        self.balance_history: list = [
            {"game": 0, "balance": starting_balance, "net_pnl": Decimal("0.00")}
        ]

    def record(self, game_number: int, new_balance: Decimal):
        self.current_balance = new_balance
        self.balance_history.append({
            "game":    game_number,
            "balance": new_balance,
            "net_pnl": new_balance - self.starting_balance
        })

    @property
    def net_profit_loss(self) -> Decimal:
        return self.current_balance - self.starting_balance

    def peak_balance(self) -> Decimal:
        return max(e["balance"] for e in self.balance_history)

    def lowest_balance(self) -> Decimal:
        return min(e["balance"] for e in self.balance_history)

    def get_pnl_progression(self) -> list:
        """Returns just the net P&L at each game — useful for charting."""
        return [e["net_pnl"] for e in self.balance_history]


class WinLossStatistics:
    """
    Comprehensive win/loss analysis for a session.
    Call record_game() after every settled bet.
    RunningTotals is embedded here — access via self.totals.
    """

    def __init__(self, session_id: str, starting_balance: Decimal):
        self.session_id = session_id
        self.totals     = RunningTotals(starting_balance)

       
        self.total_games   = 0
        self.total_wins    = 0
        self.total_losses  = 0
        self.total_pushes  = 0      

       
        self.total_wagered  = Decimal("0.00")
        self.total_winnings = Decimal("0.00")   # sum of all payouts on wins
        self.total_lost     = Decimal("0.00")   # sum of all bet amounts on losses

       
        self._win_amounts:  list = []
        self._loss_amounts: list = []

   
        self.current_win_streak    = 0
        self.current_loss_streak   = 0
        self.longest_win_streak    = 0
        self.longest_loss_streak   = 0

   

    def record_game(self, won: bool, bet_amount: Decimal,
                    payout_amount: Decimal, new_balance: Decimal):
        """
        won           — True/False outcome
        bet_amount    — amount wagered
        payout_amount — total payout if won (0 if lost)
        new_balance   — stake after this game resolves
        """
        self.total_games   += 1
        self.total_wagered += bet_amount
        self.totals.record(self.total_games, new_balance)

        if won:
            profit = payout_amount - bet_amount   
            self.total_wins     += 1
            self.total_winnings += payout_amount
            self._win_amounts.append(profit)

            self.current_win_streak  += 1
            self.current_loss_streak  = 0
            self.longest_win_streak   = max(
                self.longest_win_streak, self.current_win_streak)
        else:
            self.total_losses   += 1
            self.total_lost     += bet_amount
            self._loss_amounts.append(bet_amount)

            self.current_loss_streak += 1
            self.current_win_streak   = 0
            self.longest_loss_streak  = max(
                self.longest_loss_streak, self.current_loss_streak)



    @property
    def win_rate(self) -> Decimal:
        if self.total_games == 0:
            return Decimal("0.00")
        return round(
            Decimal(self.total_wins) / Decimal(self.total_games) * 100, 2)

    @property
    def loss_rate(self) -> Decimal:
        if self.total_games == 0:
            return Decimal("0.00")
        return round(
            Decimal(self.total_losses) / Decimal(self.total_games) * 100, 2)

    @property
    def average_win(self) -> Decimal:
        if not self._win_amounts:
            return Decimal("0.00")
        return round(sum(self._win_amounts) / len(self._win_amounts), 2)

    @property
    def average_loss(self) -> Decimal:
        if not self._loss_amounts:
            return Decimal("0.00")
        return round(sum(self._loss_amounts) / len(self._loss_amounts), 2)

    @property
    def largest_win(self) -> Decimal:
        return max(self._win_amounts)  if self._win_amounts  else Decimal("0.00")

    @property
    def largest_loss(self) -> Decimal:
        return max(self._loss_amounts) if self._loss_amounts else Decimal("0.00")

    @property
    def profit_factor(self) -> Decimal:
        """
        Total winnings / total lost.
        > 1.0 means profitable overall, < 1.0 means losing overall.
        Returns 0 if no losses yet.
        """
        if self.total_lost == 0:
            return Decimal("0.00")
        return round(self.total_winnings / self.total_lost, 4)

    @property
    def net_profit_loss(self) -> Decimal:
        return self.totals.net_profit_loss



    def get_summary(self) -> dict:
        return {
            "session_id":          self.session_id,
            "total_games":         self.total_games,
            "total_wins":          self.total_wins,
            "total_losses":        self.total_losses,
            "win_rate":            self.win_rate,
            "loss_rate":           self.loss_rate,
            "total_wagered":       self.total_wagered,
            "total_winnings":      self.total_winnings,
            "total_lost":          self.total_lost,
            "net_profit_loss":     self.net_profit_loss,
            "average_win":         self.average_win,
            "average_loss":        self.average_loss,
            "largest_win":         self.largest_win,
            "largest_loss":        self.largest_loss,
            "profit_factor":       self.profit_factor,
            "current_win_streak":  self.current_win_streak,
            "current_loss_streak": self.current_loss_streak,
            "longest_win_streak":  self.longest_win_streak,
            "longest_loss_streak": self.longest_loss_streak,
            "peak_balance":        self.totals.peak_balance(),
            "lowest_balance":      self.totals.lowest_balance(),
        }

    def print_summary(self):
        s        = self.get_summary()
        pnl_sign = "+" if s["net_profit_loss"] >= 0 else ""
        print(f"\n{'='*55}")
        print(f"  WIN/LOSS STATISTICS — Session {self.session_id[:8]}...")
        print(f"{'='*55}")
        print(f"  Games          : {s['total_games']}")
        print(f"  Wins / Losses  : {s['total_wins']} / {s['total_losses']}")
        print(f"  Win Rate       : {s['win_rate']}%")
        print(f"  Loss Rate      : {s['loss_rate']}%")
        print(f"  --")
        print(f"  Total Wagered  : ${s['total_wagered']:,.2f}")
        print(f"  Total Winnings : ${s['total_winnings']:,.2f}")
        print(f"  Total Lost     : ${s['total_lost']:,.2f}")
        print(f"  Net P&L        : {pnl_sign}${s['net_profit_loss']:,.2f}")
        print(f"  Profit Factor  : {s['profit_factor']}")
        print(f"  --")
        print(f"  Avg Win        : ${s['average_win']:,.2f}")
        print(f"  Avg Loss       : ${s['average_loss']:,.2f}")
        print(f"  Largest Win    : ${s['largest_win']:,.2f}")
        print(f"  Largest Loss   : ${s['largest_loss']:,.2f}")
        print(f"  --")
        print(f"  Cur Win Streak : {s['current_win_streak']}")
        print(f"  Cur Loss Streak: {s['current_loss_streak']}")
        print(f"  Best Streak    : {s['longest_win_streak']} wins")
        print(f"  Worst Streak   : {s['longest_loss_streak']} losses")
        print(f"  --")
        print(f"  Peak Balance   : ${s['peak_balance']:,.2f}")
        print(f"  Lowest Balance : ${s['lowest_balance']:,.2f}")
        print(f"{'='*55}")