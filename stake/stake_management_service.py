from decimal import Decimal
from helper.transaction_type import TransactionType
from stake.stake_transaction import StakeTransaction
from stake.stake_boundary import StakeBoundary
from stake.stake_monitor import StakeMonitor
from stake.stake_history_report import StakeHistoryReport


class StakeManagementService:

    def __init__(self):
        
        self._monitors: dict[str, StakeMonitor] = {}


    def _record(self, gambler_id: str, session_id: str,
                tx_type: TransactionType, amount: Decimal,
                balance_before: Decimal, balance_after: Decimal,
                bet_id: str = None, notes: str = None) -> StakeTransaction:
        tx = StakeTransaction(
            gambler_id=gambler_id,
            session_id=session_id,
            transaction_type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            bet_id=bet_id,
            notes=notes
        )
        tx.save()

      
        if session_id in self._monitors:
            self._monitors[session_id].record_change(balance_after, tx_type.value)

        return tx

  

    def initialize_stake(self, gambler_id: str, session_id: str,
                         initial_stake: Decimal,
                         boundary: StakeBoundary) -> StakeTransaction:
        """
        Validates initial stake against boundaries then records the
        INITIAL_STAKE transaction and creates a StakeMonitor for the session.
        """
        validation = boundary.validate(initial_stake)
        if not validation["is_valid"]:
            raise ValueError(
                f"Initial stake failed boundary check: {validation['errors']}")
        for w in validation["warnings"]:
            print(f"[WARN] {w}")

        self._monitors[session_id] = StakeMonitor(session_id, initial_stake)

        tx = self._record(
            gambler_id=gambler_id,
            session_id=session_id,
            tx_type=TransactionType.INITIAL_STAKE,
            amount=initial_stake,
            balance_before=Decimal("0.00"),
            balance_after=initial_stake,
            notes="Session initialized"
        )
        print(f"[INIT] Session {session_id} started with stake ${initial_stake}")
        return tx

 

    def get_current_balance(self, session_id: str) -> Decimal:
        """Returns the real-time balance from the in-memory monitor."""
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}. "
                             "Call initialize_stake first.")
        return monitor.current_stake

    def deposit(self, gambler_id: str, session_id: str,
                amount: Decimal, boundary: StakeBoundary) -> StakeTransaction:
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        balance_before = monitor.current_stake
        balance_after  = balance_before + amount

        validation = boundary.validate(balance_after)
        if not validation["is_valid"]:
            raise ValueError(f"Deposit would breach boundary: {validation['errors']}")
        for w in validation["warnings"]:
            print(f"[WARN] {w}")

        tx = self._record(gambler_id, session_id, TransactionType.DEPOSIT,
                          amount, balance_before, balance_after, notes="Deposit")
        print(f"[DEPOSIT] +${amount} → balance ${balance_after}")
        return tx

    def withdraw(self, gambler_id: str, session_id: str,
                 amount: Decimal, boundary: StakeBoundary) -> StakeTransaction:
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        balance_before = monitor.current_stake
        balance_after  = balance_before - amount

        validation = boundary.validate(balance_after)
        if not validation["is_valid"]:
            raise ValueError(f"Withdrawal would breach boundary: {validation['errors']}")
        for w in validation["warnings"]:
            print(f"[WARN] {w}")

        tx = self._record(gambler_id, session_id, TransactionType.WITHDRAWAL,
                          amount, balance_before, balance_after, notes="Withdrawal")
        print(f"[WITHDRAWAL] -${amount} → balance ${balance_after}")
        return tx

   

    def process_bet_placed(self, gambler_id: str, session_id: str,
                           bet_id: str, bet_amount: Decimal) -> StakeTransaction:
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")
        if bet_amount > monitor.current_stake:
            raise ValueError("Insufficient balance to place bet")

        balance_before = monitor.current_stake
        balance_after  = balance_before - bet_amount   # stake reserved for bet

        tx = self._record(gambler_id, session_id, TransactionType.BET_PLACED,
                          bet_amount, balance_before, balance_after,
                          bet_id=bet_id, notes=f"Bet placed: {bet_id}")
        print(f"[BET_PLACED] Bet {bet_id} — reserved ${bet_amount} → balance ${balance_after}")
        return tx

    def process_bet_win(self, gambler_id: str, session_id: str,
                        bet_id: str, win_amount: Decimal) -> StakeTransaction:
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")

        balance_before = monitor.current_stake
        balance_after  = balance_before + win_amount

        tx = self._record(gambler_id, session_id, TransactionType.BET_WIN,
                          win_amount, balance_before, balance_after,
                          bet_id=bet_id, notes=f"Bet won: {bet_id}")
        print(f"[BET_WIN] Bet {bet_id} — won ${win_amount} → balance ${balance_after}")
        return tx

    def process_bet_loss(self, gambler_id: str, session_id: str,
                         bet_id: str, loss_amount: Decimal) -> StakeTransaction:
        """
        On a loss the stake was already deducted at BET_PLACED,
        so we just record the loss event for the audit trail.
        """
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")

        balance_before = monitor.current_stake
        balance_after  = balance_before  

        tx = self._record(gambler_id, session_id, TransactionType.BET_LOSS,
                          loss_amount, balance_before, balance_after,
                          bet_id=bet_id, notes=f"Bet lost: {bet_id}")
        print(f"[BET_LOSS] Bet {bet_id} — lost ${loss_amount} → balance ${balance_after}")
        return tx



    def get_fluctuation_analysis(self, session_id: str) -> dict:
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")
        return monitor.get_fluctuation_analysis()



    def validate_stake(self, session_id: str,
                       boundary: StakeBoundary) -> dict:
        monitor = self._monitors.get(session_id)
        if not monitor:
            raise ValueError(f"No active monitor for session {session_id}")
        result = boundary.validate(monitor.current_stake)
        if result["warnings"]:
            for w in result["warnings"]:
                print(f"[WARN] {w}")
        if not result["is_valid"]:
            for e in result["errors"]:
                print(f"[ERROR] {e}")
        return result



    def generate_report(self, gambler_id: str,
                        session_id: str) -> StakeHistoryReport:
        transactions = StakeTransaction.find_by_session(session_id)
        report = StakeHistoryReport(gambler_id, session_id, transactions)
        print(f"[REPORT] Generated for session {session_id} "
              f"— {report.total_transactions} transactions")
        return report

    def generate_full_gambler_report(self, gambler_id: str) -> StakeHistoryReport:
        """Cross-session report — all transactions for this gambler."""
        transactions = StakeTransaction.find_by_gambler(gambler_id)
        report = StakeHistoryReport(gambler_id, "ALL_SESSIONS", transactions)
        print(f"[REPORT] Full gambler report — {report.total_transactions} transactions")
        return report