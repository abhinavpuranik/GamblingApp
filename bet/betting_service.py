import random
from decimal import Decimal
from bet.bet import Bet
from bet.betting_session import BettingSession
from bet.betting_strategy import BettingStrategy


class BettingService:

    # ── Use Case 1: Place a single bet ────────────────────────────────────────

    def place_bet(self, betting_session: BettingSession,
                  gambler_id: str, bet_amount: Decimal,
                  win_probability: Decimal, odds_type: str,
                  odds_value: Decimal, strategy_id: int = 0) -> Bet:
        """
        Validates amount, creates the Bet, deducts from session stake,
        saves to DB, returns the unsettled Bet.
        Call settle_bet() immediately after to resolve the outcome.
        """
        current_stake = betting_session.current_stake
        game_index    = len(betting_session.bets) + 1

        # Bet.__init__ validates amount > 0, probability range, and stake availability
        bet = Bet(
            session_id=betting_session.session_id,
            gambler_id=gambler_id,
            strategy_id=strategy_id,
            game_index=game_index,
            bet_amount=bet_amount,
            win_probability=win_probability,
            odds_type=odds_type,
            odds_value=odds_value,
            stake_before=current_stake
        )

        # deduct bet from session stake immediately (reserved)
        betting_session.current_stake -= bet_amount
        bet.save()

        print(f"[BET PLACED] Game {game_index} — "
              f"${bet_amount} at {float(win_probability)*100:.1f}% prob "
              f"| potential win: ${bet.potential_win} "
              f"| stake: ${current_stake} → ${betting_session.current_stake}")
        return bet

    # ── Use Case 2: Determine outcome ─────────────────────────────────────────

    def determine_outcome(self, bet: Bet) -> bool:
        """
        Rolls against win_probability and returns True (win) or False (loss).
        Result is stored on the Bet object itself.
        """
        won = bet.determine_outcome()
        outcome_str = "WON" if won else "LOST"
        print(f"[OUTCOME] Bet {bet.bet_id[:8]}... — {outcome_str} "
              f"(roll vs {float(bet.win_probability)*100:.1f}% threshold)")
        return won

    # ── Use Case 3: Settle bet and apply to stake ─────────────────────────────

    def settle_bet(self, bet: Bet,
                   betting_session: BettingSession) -> Decimal:
        """
        Applies win/loss to the session's current stake and persists the result.
        Returns the new stake.
        """
        new_stake = bet.settle(betting_session.current_stake)
        betting_session.add_bet(bet)
        bet.update_settlement()

        result_str = f"+${bet.potential_win}" if bet.won else f"-${bet.bet_amount}"
        print(f"[SETTLED] Bet {bet.bet_id[:8]}... — {result_str} "
              f"| new stake: ${new_stake}")
        return new_stake

    # ── Use Case 4: Validate amount (standalone helper) ───────────────────────

    def validate_bet_amount(self, amount: Decimal,
                            current_stake: Decimal,
                            min_bet: Decimal,
                            max_bet: Decimal) -> dict:
        errors = []
        if amount <= 0:
            errors.append("Bet amount must be positive")
        if amount < min_bet:
            errors.append(f"Amount ${amount} is below minimum bet ${min_bet}")
        if amount > max_bet:
            errors.append(f"Amount ${amount} exceeds maximum bet ${max_bet}")
        if amount > current_stake:
            errors.append(
                f"Amount ${amount} exceeds available stake ${current_stake}")

        return {"is_valid": len(errors) == 0, "errors": errors}

    # ── Use Case 5: Place a bet using a strategy ──────────────────────────────

    def place_bet_with_strategy(self, betting_session: BettingSession,
                                gambler_id: str,
                                strategy: BettingStrategy,
                                win_probability: Decimal,
                                odds_type: str,
                                odds_value: Decimal,
                                min_bet: Decimal,
                                max_bet: Decimal) -> Bet:
        """
        Asks the strategy to calculate the next bet amount based on the
        last bet's result, validates it, then delegates to place_bet().
        """
        bets     = betting_session.bets
        last_bet = bets[-1] if bets else None

        amount = strategy.calculate_bet_amount(
            current_stake=betting_session.current_stake,
            last_bet=last_bet.bet_amount if last_bet else None,
            last_won=last_bet.won        if last_bet else None
        )

        # clamp to min/max and available stake
        amount = max(min_bet, min(amount, max_bet, betting_session.current_stake))

        validation = self.validate_bet_amount(
            amount, betting_session.current_stake, min_bet, max_bet)
        if not validation["is_valid"]:
            raise ValueError(f"Strategy bet invalid: {validation['errors']}")

        print(f"[STRATEGY] {strategy.__class__.__name__} → bet ${amount}")
        return self.place_bet(
            betting_session, gambler_id, amount,
            win_probability, odds_type, odds_value
        )

    # ── Use Case 6: Multiple consecutive bets ─────────────────────────────────

    def place_consecutive_bets(self, betting_session: BettingSession,
                               gambler_id: str,
                               strategy: BettingStrategy,
                               num_bets: int,
                               win_probability: Decimal,
                               odds_type: str,
                               odds_value: Decimal,
                               min_bet: Decimal,
                               max_bet: Decimal,
                               stop_on_zero: bool = True) -> BettingSession:
        """
        Runs num_bets bets back-to-back using the given strategy.
        Stops early if:
          - stake drops to 0 (when stop_on_zero=True)
          - strategy can't produce a valid bet amount
        Returns the updated BettingSession.
        """
        print(f"\n[CONSECUTIVE] Starting {num_bets} bets with "
              f"{strategy.__class__.__name__}")
        print("-" * 52)

        for i in range(num_bets):
            if stop_on_zero and betting_session.current_stake <= 0:
                print(f"[CONSECUTIVE] Stopped early at bet {i+1} — stake depleted")
                break

            try:
                bet = self.place_bet_with_strategy(
                    betting_session, gambler_id, strategy,
                    win_probability, odds_type, odds_value,
                    min_bet, max_bet
                )
                self.determine_outcome(bet)
                self.settle_bet(bet, betting_session)

            except ValueError as e:
                print(f"[CONSECUTIVE] Stopped at bet {i+1} — {e}")
                break

        betting_session.end()
        strategy.reset()
        return betting_session