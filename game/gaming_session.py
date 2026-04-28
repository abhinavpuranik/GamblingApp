import uuid
from datetime import datetime
from decimal import Decimal
from db import get_connection
from session.session_enum import SessionStatus, SessionEndReason
from session.session_parameters import SessionParameters
from game.pause_record import PauseRecord
from game.pause_record import PauseHistory
from game.game_record import GameRecord, GameOutcome
from bet.bet import Bet
from bet.betting_strategy import BettingStrategy
from helper.win_loss_statistics import WinLossStatistics
from bet.betting_strategy import OutcomeStrategy, RandomOutcomeStrategy
from helper.odds_config import OddsConfiguration, OddsType


class GamingSession:
    def __init__(self, gambler_id: str, params: SessionParameters,
                 starting_stake: Decimal):

        
        self.session_id     = str(uuid.uuid4())
        self.gambler_id     = gambler_id
        self.params         = params

        
        self.starting_stake = starting_stake
        self.current_stake  = starting_stake
        self.peak_stake     = starting_stake
        self.lowest_stake   = starting_stake

      
        self.status     = SessionStatus.INITIALIZED
        self.end_reason = None

        
        self.started_at = None
        self.ended_at   = None

        
        self.games_played           = 0
        self.game_records: list     = []
        self.consecutive_wins       = 0
        self.consecutive_losses     = 0


        self.pause_history = PauseHistory(self.session_id)

        self.win_loss_stats = WinLossStatistics(self.session_id, starting_stake)
        self.outcome_strategy: OutcomeStrategy = RandomOutcomeStrategy()  # default

    
    def start(self):
        if self.status != SessionStatus.INITIALIZED:
            raise Exception(
                f"Cannot start session — current status: {self.status.value}")

        boundary_check = self.params.validate_stake(self.current_stake)
        if not boundary_check["is_valid"]:
            raise ValueError(
                f"Starting stake ${self.current_stake} fails boundary check: "
                f"{boundary_check['errors']}")

        self.status     = SessionStatus.ACTIVE
        self.started_at = datetime.now()

  
        self._save()

        print(f"[SESSION START] {self.session_id[:8]}... | "
              f"stake: ${self.current_stake} | "
              f"limits: ${self.params.lower_limit} — ${self.params.upper_limit}")

 

    def play_game(self, strategy: BettingStrategy,
                  odds_type: str = "FIXED",
                  odds_value: Decimal = Decimal("1.90"),
                  odds_config_id: str = None) -> GameRecord:

        self._assert_active()
        if not self._check_time_and_game_limits():
            print("[INFO] Session ended gracefully")
            return None


        last_record = self.game_records[-1] if self.game_records else None
        last_bet    = Decimal(str(last_record.bet_amount)) if last_record else None
        last_won    = (last_record.outcome == GameOutcome.WIN) if last_record else None

        bet_amount = strategy.calculate_bet_amount(
            current_stake=self.current_stake,
            last_bet=last_bet,
            last_won=last_won
        )

   
        bet_amount = max(self.params.min_bet,
                         min(bet_amount, self.params.max_bet,
                             self.current_stake))


        bet_validation = self.params.validate_bet(bet_amount)
        if not bet_validation["is_valid"]:
            raise ValueError(
                f"Bet validation failed: {bet_validation['errors']}")

    
        game_start = datetime.now()

        bet = Bet(
            session_id=self.session_id,
            gambler_id=self.gambler_id,
            strategy_id=0,
            game_index=self.games_played + 1,
            bet_amount=bet_amount,
            win_probability=self.params.default_win_probability,
            odds_type=odds_type,
            odds_value=odds_value,
            stake_before=self.current_stake
        )


        self.current_stake -= bet_amount


        won = self.outcome_strategy.determine_outcome(self.params.default_win_probability)
        bet.won = won
        bet.settle(self.current_stake)
        bet.save()
        bet.update_settlement()


        self.current_stake = bet.stake_after


        if won:
            self.consecutive_wins  += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.consecutive_wins   = 0

       
        self.peak_stake   = max(self.peak_stake,   self.current_stake)
        self.lowest_stake = min(self.lowest_stake, self.current_stake)
        self.games_played += 1
        self.win_loss_stats.record_game(
            won=won,
            bet_amount=bet_amount,
            payout_amount=bet.potential_win if won else Decimal("0.00"),
            new_balance=self.current_stake
        )

    
        duration_ms = int(
            (datetime.now() - game_start).total_seconds() * 1000)

        record = GameRecord.from_bet(
            bet=bet,
            session_id=self.session_id,
            odds_config_id=odds_config_id or "default",
            consecutive_win_streak=self.consecutive_wins,
            consecutive_loss_streak=self.consecutive_losses,
            game_duration_ms=duration_ms
        )
        record.save()
        self.game_records.append(record)

        outcome_str = "WON" if won else "LOST"
        print(f"  [GAME {self.games_played:>3}] {outcome_str} | "
              f"bet: ${bet_amount} | "
              f"stake: ${bet.stake_before} → ${self.current_stake} | "
              f"streak W{self.consecutive_wins}/L{self.consecutive_losses}")

   
        self._update()


        self._check_boundaries()

        return record


    def pause(self, reason: str) -> PauseRecord:
        self._assert_active()

        self.status = SessionStatus.PAUSED
        pause = PauseRecord(self.session_id, reason)
        pause.save()
        self.pause_history.add(pause)
        self._update()

        print(f"[PAUSE] Session paused — reason: {reason} | "
              f"total pauses so far: {self.pause_history.get_pause_count()}")
        return pause

    def resume(self) -> PauseRecord:
        if self.status != SessionStatus.PAUSED:
            raise Exception(
                f"Cannot resume — session is not paused "
                f"(current status: {self.status.value})")

        active_pause = self.pause_history.get_active_pause()
        if not active_pause:
            raise Exception("No active pause found to resume")

        active_pause.resume()
        active_pause.update_resume()

        self.status = SessionStatus.ACTIVE
        self._update()

        print(f"[RESUME] Session resumed | "
              f"pause duration: {active_pause.pause_seconds}s | "
              f"total paused: {self.pause_history.get_total_pause_seconds()}s")
        return active_pause



    def _check_boundaries(self):
        result = self.params.validate_stake(self.current_stake)

        for warning in result["warnings"]:
            print(f"  [BOUNDARY WARN] {warning}")

        if not result["is_valid"]:
            if self.current_stake >= self.params.upper_limit:
                self._end(SessionStatus.ENDED_WIN, SessionEndReason.UPPER_LIMIT)
            elif self.current_stake <= self.params.lower_limit:
                self._end(SessionStatus.ENDED_LOSS, SessionEndReason.LOWER_LIMIT)

    def _check_time_and_game_limits(self):

        if self.params.is_game_limit_reached(self.games_played):
            print("[SESSION END] Reason: MAX_GAMES")
            self.end_reason = "MAX_GAMES"
            self.end_manually()
            return False

        if self.params.is_time_exceeded(self.started_at):
            print("[SESSION END] Reason: TIMEOUT")
            self.end_reason = "TIMEOUT"
            self.end_manually()
            return False

        return True



    def end_manually(self):
        self._assert_active()
        self._end(SessionStatus.ENDED_MANUAL, SessionEndReason.MANUAL)

 
    def get_active_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        end            = self.ended_at if self.ended_at else datetime.now()
        total_seconds  = (end - self.started_at).total_seconds()
        paused_seconds = self.pause_history.get_total_pause_seconds()
        return max(0.0, total_seconds - paused_seconds)

    def get_total_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.ended_at if self.ended_at else datetime.now()
        return (end - self.started_at).total_seconds()
    
    

   

    def get_statistics(self) -> dict:
        wins   = [r for r in self.game_records if r.outcome == GameOutcome.WIN]
        losses = [r for r in self.game_records if r.outcome == GameOutcome.LOSS]

        total_wagered = sum(r.bet_amount    for r in self.game_records)
        total_won     = sum(r.payout_amount for r in wins)
        net_change    = self.current_stake  - self.starting_stake

        win_rate = (
            round(Decimal(len(wins)) / Decimal(self.games_played) * 100, 2)
            if self.games_played > 0 else Decimal("0.00")
        )
        avg_bet = (
            round(total_wagered / Decimal(self.games_played), 2)
            if self.games_played > 0 else Decimal("0.00")
        )

        return {
            "session_id":     self.session_id,
            "status":         self.status.value,
            "end_reason":     self.end_reason.value if self.end_reason else None,
            "starting_stake": self.starting_stake,
            "current_stake":  self.current_stake,
            "peak_stake":     self.peak_stake,
            "lowest_stake":   self.lowest_stake,
            "net_change":     net_change,
            "games_played":   self.games_played,
            "total_wins":     len(wins),
            "total_losses":   len(losses),
            "win_rate":       win_rate,
            "total_wagered":  total_wagered,
            "total_won":      total_won,
            "avg_bet":        avg_bet,
            "active_seconds": round(self.get_active_seconds(), 2),
            "total_seconds":  round(self.get_total_seconds(), 2),
            "total_pauses":   self.pause_history.get_pause_count(),
            "paused_seconds": self.pause_history.get_total_pause_seconds(),
        }
    
    def set_outcome_strategy(self, strategy: OutcomeStrategy):
        self.outcome_strategy = strategy

    def print_summary(self):
        s        = self.get_statistics()
        pnl_sign = "+" if s["net_change"] >= 0 else ""
        print(f"\n{'='*55}")
        print(f"  GAMING SESSION SUMMARY")
        print(f"  ID     : {self.session_id[:8]}...")
        print(f"  Status : {s['status']}")
        if s["end_reason"]:
            print(f"  Ended  : {s['end_reason']}")
        print(f"{'='*55}")
        print(f"  Starting Stake : ${s['starting_stake']:,.2f}")
        print(f"  Current Stake  : ${s['current_stake']:,.2f}")
        print(f"  Peak Stake     : ${s['peak_stake']:,.2f}")
        print(f"  Lowest Stake   : ${s['lowest_stake']:,.2f}")
        print(f"  Net P&L        : {pnl_sign}${s['net_change']:,.2f}")
        print(f"  --")
        print(f"  Games Played   : {s['games_played']}")
        print(f"  Wins / Losses  : {s['total_wins']} / {s['total_losses']}")
        print(f"  Win Rate       : {s['win_rate']}%")
        print(f"  Total Wagered  : ${s['total_wagered']:,.2f}")
        print(f"  Total Won      : ${s['total_won']:,.2f}")
        print(f"  Avg Bet        : ${s['avg_bet']:,.2f}")
        print(f"  --")
        print(f"  Total Time     : {s['total_seconds']}s")
        print(f"  Active Time    : {s['active_seconds']}s")
        print(f"  Paused Time    : {s['paused_seconds']}s")
        print(f"  Total Pauses   : {s['total_pauses']}")
        print(f"{'='*55}")

   
    def _assert_active(self):
        if self.status != SessionStatus.ACTIVE:
            raise Exception(
                f"Session is not active "
                f"(current status: {self.status.value})")

    def _is_already_ended(self) -> bool:
        return self.status in (
            SessionStatus.ENDED_WIN,
            SessionStatus.ENDED_LOSS,
            SessionStatus.ENDED_MANUAL,
            SessionStatus.ENDED_TIMEOUT
        )

    def _end(self, status: SessionStatus, reason: SessionEndReason):
        if self._is_already_ended():
            return  # never end twice

        self.status     = status
        self.end_reason = reason
        self.ended_at   = datetime.now()
        self._update()

        print(f"[SESSION END] Status: {status.value} | "
              f"Reason: {reason.value} | "
              f"Final stake: ${self.current_stake}")

    
    def _save(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO SESSIONS (
                    session_id, gambler_id, status, end_reason,
                    starting_stake, ending_stake, peak_stake, lowest_stake,
                    max_games, games_played, total_pause_seconds,
                    started_at, ended_at, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (self.session_id, self.gambler_id,
                  self.status.value,
                  self.end_reason.value if self.end_reason else None,
                  self.starting_stake,
                  None,                   # ending_stake — not known yet
                  self.peak_stake,
                  self.lowest_stake,
                  self.params.maximum_games,
                  self.games_played,
                  self.pause_history.get_total_pause_seconds(),
                  self.started_at,
                  self.ended_at,
                  self.started_at))       # created_at = started_at
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def _update(self):
        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE SESSIONS
                SET status               = %s,
                    end_reason           = %s,
                    ending_stake         = %s,
                    peak_stake           = %s,
                    lowest_stake         = %s,
                    games_played         = %s,
                    total_pause_seconds  = %s,
                    ended_at             = %s
                WHERE session_id = %s
            """, (self.status.value,
                  self.end_reason.value if self.end_reason else None,
                  self.current_stake,
                  self.peak_stake,
                  self.lowest_stake,
                  self.games_played,
                  self.pause_history.get_total_pause_seconds(),
                  self.ended_at,
                  self.session_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()



class GameSessionManager:

    def __init__(self):
        self._active_sessions:    dict[str, GamingSession] = {}
        self._completed_sessions: dict[str, GamingSession] = {}

    def start_session(self, gambler_id: str,
                      params: SessionParameters,
                      starting_stake: Decimal) -> GamingSession:
        self._assert_no_active_session(gambler_id)
        session = GamingSession(gambler_id, params, starting_stake)
        session.start()
        self._active_sessions[gambler_id] = session
        print(f"[MANAGER] Session {session.session_id[:8]}... "
              f"started for gambler {gambler_id[:8]}...")
        return session

    def pause_session(self, gambler_id: str, reason: str):
        self._get_active_session(gambler_id).pause(reason)

    def resume_session(self, gambler_id: str):
        self._get_active_session(gambler_id).resume()

    def end_session(self, gambler_id: str):
        session = self._get_active_session(gambler_id)
        session.end_manually()
        self._move_to_completed(gambler_id)

    def play_game(self, gambler_id: str,
                  strategy: BettingStrategy,
                  odds_type: str = "FIXED",
                  odds_value: Decimal = Decimal("1.90"),
                  odds_config_id: str = None) -> GameRecord:
        session = self._get_active_session(gambler_id)
        record  = session.play_game(strategy, odds_type,
                                    odds_value, odds_config_id)
        if self._is_ended(session):
            self._move_to_completed(gambler_id)
        return record

    def has_active_session(self, gambler_id: str) -> bool:
        return gambler_id in self._active_sessions

    def get_active_session(self, gambler_id: str) -> GamingSession:
        return self._get_active_session(gambler_id)

    def get_completed_sessions(self, gambler_id: str = None) -> list:
        sessions = list(self._completed_sessions.values())
        if gambler_id:
            sessions = [s for s in sessions if s.gambler_id == gambler_id]
        return sessions

    def get_session_by_id(self, session_id: str) -> GamingSession:
        for session in self._active_sessions.values():
            if session.session_id == session_id:
                return session
        if session_id in self._completed_sessions:
            return self._completed_sessions[session_id]
        raise ValueError(f"No session found with ID: {session_id}")

    def get_active_session_report(self, gambler_id: str) -> dict:
        return self._get_active_session(gambler_id).get_statistics()

    def get_completed_session_report(self, session_id: str) -> dict:
        if session_id not in self._completed_sessions:
            raise ValueError(f"No completed session found: {session_id}")
        return self._completed_sessions[session_id].get_statistics()

    def get_gambler_summary(self, gambler_id: str) -> dict:
        completed = self.get_completed_sessions(gambler_id)
        if not completed:
            return {"gambler_id": gambler_id,
                    "total_sessions": 0,
                    "message": "No completed sessions found"}

        total_games  = sum(s.games_played for s in completed)
        total_wins   = sum(
            len([r for r in s.game_records if r.outcome == GameOutcome.WIN])
            for s in completed)
        total_losses = total_games - total_wins
        net_change   = sum(
            s.current_stake - s.starting_stake for s in completed)
        win_rate     = (
            round(Decimal(total_wins) / Decimal(total_games) * 100, 2)
            if total_games > 0 else Decimal("0.00"))

        return {
            "gambler_id":          gambler_id,
            "total_sessions":      len(completed),
            "win_sessions":        len([s for s in completed
                                        if s.status == SessionStatus.ENDED_WIN]),
            "loss_sessions":       len([s for s in completed
                                        if s.status == SessionStatus.ENDED_LOSS]),
            "total_games":         total_games,
            "total_wins":          total_wins,
            "total_losses":        total_losses,
            "win_rate":            win_rate,
            "net_change":          net_change,
            "best_session_stake":  max(s.peak_stake    for s in completed),
            "worst_session_stake": min(s.lowest_stake  for s in completed),
        }

    def print_all_active(self):
        if not self._active_sessions:
            print("[MANAGER] No active sessions")
            return
        print(f"\n[MANAGER] Active Sessions ({len(self._active_sessions)}):")
        print("-" * 52)
        for gambler_id, session in self._active_sessions.items():
            print(f"  Gambler : {gambler_id[:8]}... | "
                  f"Session : {session.session_id[:8]}... | "
                  f"Status  : {session.status.value} | "
                  f"Stake   : ${session.current_stake} | "
                  f"Games   : {session.games_played}")

    def print_gambler_summary(self, gambler_id: str):
        s        = self.get_gambler_summary(gambler_id)
        pnl_sign = "+" if s.get("net_change", 0) >= 0 else ""
        print(f"\n{'='*52}")
        print(f"  GAMBLER LIFETIME SUMMARY")
        print(f"  Gambler : {gambler_id[:8]}...")
        print(f"{'='*52}")
        if s.get("total_sessions", 0) == 0:
            print(f"  No completed sessions.")
        else:
            print(f"  Total Sessions  : {s['total_sessions']}")
            print(f"  Win/Loss Sess   : {s['win_sessions']} / {s['loss_sessions']}")
            print(f"  Total Games     : {s['total_games']}")
            print(f"  Wins / Losses   : {s['total_wins']} / {s['total_losses']}")
            print(f"  Win Rate        : {s['win_rate']}%")
            print(f"  Net P&L         : {pnl_sign}${s['net_change']:,.2f}")
            print(f"  Best Peak Stake : ${s['best_session_stake']:,.2f}")
            print(f"  Worst Low Stake : ${s['worst_session_stake']:,.2f}")
        print(f"{'='*52}")


    def _get_active_session(self, gambler_id: str) -> GamingSession:
        if gambler_id not in self._active_sessions:
            raise ValueError(
                f"No active session for gambler {gambler_id}. "
                f"Call start_session() first.")
        return self._active_sessions[gambler_id]

    def _assert_no_active_session(self, gambler_id: str):
        if gambler_id in self._active_sessions:
            existing = self._active_sessions[gambler_id]
            raise Exception(
                f"Gambler {gambler_id[:8]}... already has an active session "
                f"({existing.session_id[:8]}...). "
                f"End it before starting a new one.")

    def _is_ended(self, session: GamingSession) -> bool:
        return session.status in (
            SessionStatus.ENDED_WIN,
            SessionStatus.ENDED_LOSS,
            SessionStatus.ENDED_MANUAL,
            SessionStatus.ENDED_TIMEOUT
        )

    def _move_to_completed(self, gambler_id: str):
        session = self._active_sessions.pop(gambler_id)
        self._completed_sessions[session.session_id] = session
        print(f"[MANAGER] Session {session.session_id[:8]}... "
              f"moved to completed | status: {session.status.value}")