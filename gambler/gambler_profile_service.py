from decimal import Decimal
from gambler.gambler import GamblingProfile
from bet.betting_preferences import BettingPreferences
from gambler.gambler_statistics import GamblerStatistics


class GamblerProfileService:

    

    def create_gambler(self, username: str, full_name: str, email: str,
                       initial_stake: Decimal, win_threshold: Decimal,
                       loss_threshold: Decimal, min_required_stake: Decimal,
                       min_bet: Decimal, max_bet: Decimal,
                       preferred_game_type: str, auto_play_enabled: bool,
                       auto_play_max_games: int, session_loss_limit: Decimal,
                       session_win_target: Decimal) -> GamblingProfile:
        """
        Creates a GamblingProfile + BettingPreferences together.
        Validates all stake/threshold requirements before persisting.
        """
        # GamblingProfile.__init__ validates stake/threshold rules internally
        gambler = GamblingProfile(
            username=username,
            full_name=full_name,
            email=email,
            initial_stake=initial_stake,
            win_threshold=win_threshold,
            loss_threshold=loss_threshold,
            min_required_stake=min_required_stake
        )
        gambler.save()

        # BettingPreferences.__init__ validates bet amount rules internally
        prefs = BettingPreferences(
            gambler_id=gambler.gambler_id,
            min_bet=min_bet,
            max_bet=max_bet,
            preferred_game_type=preferred_game_type,
            auto_play_enabled=auto_play_enabled,
            auto_play_max_games=auto_play_max_games,
            session_loss_limit=session_loss_limit,
            session_win_target=session_win_target
        )
        prefs.save()

        print(f"[CREATE] Gambler '{username}' created with ID: {gambler.gambler_id}")
        return gambler

   

    def update_personal_info(self, gambler: GamblingProfile,
                             new_full_name: str = None,
                             new_email: str = None,
                             new_username: str = None):
        """Updates personal fields. Only changes what's provided."""
        if new_full_name:
            gambler.full_name = new_full_name
        if new_email:
            gambler.email = new_email
        if new_username:
            gambler.username = new_username

        from datetime import datetime
        gambler.updated_at = datetime.now()
        gambler.update_personal_info()
        print(f"[UPDATE] Personal info updated for gambler: {gambler.gambler_id}")

    def update_thresholds(self, gambler: GamblingProfile,
                          new_win_threshold: Decimal = None,
                          new_loss_threshold: Decimal = None):
        """Updates win/loss thresholds with validation."""
        win  = new_win_threshold  if new_win_threshold  else gambler.win_threshold
        loss = new_loss_threshold if new_loss_threshold else gambler.loss_threshold

        if win <= gambler.current_stake:
            raise ValueError("Win threshold must be greater than current stake")
        if loss >= gambler.current_stake:
            raise ValueError("Loss threshold must be less than current stake")
        if loss < gambler.min_required_stake:
            raise ValueError("Loss threshold cannot be below minimum required stake")

        from datetime import datetime
        gambler.win_threshold  = win
        gambler.loss_threshold = loss
        gambler.updated_at     = datetime.now()
        gambler.update_thresholds()
        print(f"[UPDATE] Thresholds updated for gambler: {gambler.gambler_id}")

    def update_preferences(self, prefs: BettingPreferences,
                           min_bet: Decimal = None,
                           max_bet: Decimal = None,
                           preferred_game_type: str = None,
                           auto_play_enabled: bool = None,
                           auto_play_max_games: int = None,
                           session_loss_limit: Decimal = None,
                           session_win_target: Decimal = None):
        """Updates betting preferences. Only changes what's provided."""
        if min_bet             is not None: prefs.min_bet             = min_bet
        if max_bet             is not None: prefs.max_bet             = max_bet
        if preferred_game_type is not None: prefs.preferred_game_type = preferred_game_type
        if auto_play_enabled   is not None: prefs.auto_play_enabled   = auto_play_enabled
        if auto_play_max_games is not None: prefs.auto_play_max_games = auto_play_max_games
        if session_loss_limit  is not None: prefs.session_loss_limit  = session_loss_limit
        if session_win_target  is not None: prefs.session_win_target  = session_win_target

        if prefs.min_bet > prefs.max_bet:
            raise ValueError("min_bet cannot exceed max_bet")

        prefs.update()
        print(f"[UPDATE] Preferences updated for gambler: {prefs.gambler_id}")

    

    def get_statistics(self, gambler_id: str) -> GamblerStatistics:
        """Fetches gambler + preferences from DB and returns a statistics DTO."""
        gambler_row = GamblingProfile.find_by_id(gambler_id)
        if not gambler_row:
            raise ValueError(f"Gambler not found: {gambler_id}")

        prefs_row = BettingPreferences.find_by_gambler(gambler_id)
        stats = GamblerStatistics(gambler_row, prefs_row)
        print(f"[RETRIEVE] Statistics built for gambler: {gambler_id}")
        return stats



    def validate_eligibility(self, gambler_id: str) -> dict:
        """
        Returns a dict with is_eligible (bool) and a list of reasons if not.
        Checks: account active, stake above minimum, thresholds not breached.
        """
        gambler_row = GamblingProfile.find_by_id(gambler_id)
        if not gambler_row:
            raise ValueError(f"Gambler not found: {gambler_id}")

        current_stake   = Decimal(str(gambler_row["current_stake"]))
        win_threshold   = Decimal(str(gambler_row["win_threshold"]))
        loss_threshold  = Decimal(str(gambler_row["loss_threshold"]))
        min_req         = Decimal(str(gambler_row["min_required_stake"]))
        is_active       = gambler_row["is_active"]

        reasons = []

        if not is_active:
            reasons.append("Account is inactive")
        if current_stake < min_req:
            reasons.append(
                f"Current stake ${current_stake} is below minimum ${min_req}")
        if current_stake >= win_threshold:
            reasons.append(
                f"Win threshold ${win_threshold} already reached — session should end")
        if current_stake <= loss_threshold:
            reasons.append(
                f"Loss threshold ${loss_threshold} breached — session should end")

        result = {
            "gambler_id":   gambler_id,
            "is_eligible":  len(reasons) == 0,
            "reasons":      reasons
        }

        status = "ELIGIBLE" if result["is_eligible"] else "NOT ELIGIBLE"
        print(f"[VALIDATE] Gambler {gambler_id}: {status}")
        return result

 

    def reset_profile(self, gambler: GamblingProfile, new_initial_stake: Decimal):
        """
        Resets the gambler for a new session:
        - Sets current_stake to new_initial_stake
        - Clears all stats (bets, wins, losses, winnings)
        - Recalculates win/loss thresholds proportionally based on the
          original ratio so the gambler keeps the same risk profile
        - Reactivates the account if it was deactivated
        """
        if new_initial_stake < gambler.min_required_stake:
            raise ValueError(
                f"New stake ${new_initial_stake} is below minimum ${gambler.min_required_stake}")

        # proportional threshold recalculation
        original_stake = gambler.initial_stake
        win_ratio  = gambler.win_threshold  / original_stake
        loss_ratio = gambler.loss_threshold / original_stake

        from datetime import datetime
        gambler.initial_stake   = new_initial_stake
        gambler.current_stake   = new_initial_stake
        gambler.win_threshold   = round(new_initial_stake * win_ratio,  2)
        gambler.loss_threshold  = round(new_initial_stake * loss_ratio, 2)
        gambler.total_bets      = 0
        gambler.total_wins      = 0
        gambler.total_losses    = 0
        gambler.total_winnings  = Decimal("0.00")
        gambler.is_active       = True
        gambler.updated_at      = datetime.now()

        gambler.reset_to_initial()
        print(
            f"[RESET] Gambler {gambler.gambler_id} reset. "
            f"New stake: ${new_initial_stake}, "
            f"Win threshold: ${gambler.win_threshold}, "
            f"Loss threshold: ${gambler.loss_threshold}"
        )