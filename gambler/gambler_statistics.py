from decimal import Decimal


class GamblerStatistics:
    """
    Read-only DTO — built from a GamblingProfile dict (row from DB)
    and the gambler's current BettingPreferences dict.
    Never writes to the database.
    """

    def __init__(self, gambler_row: dict, preferences_row: dict = None):
    
        self.gambler_id  = gambler_row["gambler_id"]
        self.username    = gambler_row["username"]
        self.full_name   = gambler_row["full_name"]
        self.email       = gambler_row["email"]
        self.is_active   = gambler_row["is_active"]

      
        self.initial_stake      = Decimal(str(gambler_row["initial_stake"]))
        self.current_stake      = Decimal(str(gambler_row["current_stake"]))
        self.win_threshold      = Decimal(str(gambler_row["win_threshold"]))
        self.loss_threshold     = Decimal(str(gambler_row["loss_threshold"]))
        self.min_required_stake = Decimal(str(gambler_row["min_required_stake"]))

      
        self.total_bets     = gambler_row["total_bets"]
        self.total_wins     = gambler_row["total_wins"]
        self.total_losses   = gambler_row["total_losses"]
        self.total_winnings = Decimal(str(gambler_row["total_winnings"]))

     
        self.preferences = preferences_row  # raw dict or None

       
        self.win_rate        = self._calc_win_rate()
        self.net_profit_loss = self._calc_net_profit_loss()
        self.average_bet     = self._calc_average_bet()

  
        self.win_threshold_reached  = self.current_stake >= self.win_threshold
        self.loss_threshold_reached = self.current_stake <= self.loss_threshold
        self.below_minimum_stake    = self.current_stake < self.min_required_stake



    def _calc_win_rate(self) -> Decimal:
        if self.total_bets == 0:
            return Decimal("0.00")
        return round(Decimal(self.total_wins) / Decimal(self.total_bets) * 100, 2)

    def _calc_net_profit_loss(self) -> Decimal:
        return self.current_stake - self.initial_stake

    def _calc_average_bet(self) -> Decimal:
        """
        We don't store total amount wagered, so we derive a rough average
        from total_winnings and win_rate as a best-effort.
        If you add a total_wagered column later, replace this.
        """
        if self.total_bets == 0:
            return Decimal("0.00")
        # net change per bet as a simple proxy
        return round(abs(self.net_profit_loss) / Decimal(self.total_bets), 2)


    def summary(self) -> str:
        status_flags = []
        if self.win_threshold_reached:
            status_flags.append("WIN THRESHOLD REACHED")
        if self.loss_threshold_reached:
            status_flags.append("LOSS THRESHOLD REACHED")
        if self.below_minimum_stake:
            status_flags.append("BELOW MINIMUM STAKE")
        if not status_flags:
            status_flags.append("Normal")

        pnl_sign = "+" if self.net_profit_loss >= 0 else ""

        return (
            f"\n{'='*50}\n"
            f"  GAMBLER STATISTICS: {self.username}\n"
            f"{'='*50}\n"
            f"  Name          : {self.full_name}\n"
            f"  Email         : {self.email}\n"
            f"  Active        : {self.is_active}\n"
            f"  --\n"
            f"  Initial Stake : ${self.initial_stake:,.2f}\n"
            f"  Current Stake : ${self.current_stake:,.2f}\n"
            f"  Net P&L       : {pnl_sign}${self.net_profit_loss:,.2f}\n"
            f"  Win Threshold : ${self.win_threshold:,.2f}\n"
            f"  Loss Threshold: ${self.loss_threshold:,.2f}\n"
            f"  --\n"
            f"  Total Bets    : {self.total_bets}\n"
            f"  Wins / Losses : {self.total_wins} / {self.total_losses}\n"
            f"  Win Rate      : {self.win_rate}%\n"
            f"  Total Winnings: ${self.total_winnings:,.2f}\n"
            f"  Avg Bet (est) : ${self.average_bet:,.2f}\n"
            f"  --\n"
            f"  Status        : {', '.join(status_flags)}\n"
            f"{'='*50}"
        )