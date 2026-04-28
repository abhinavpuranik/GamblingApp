from decimal import Decimal
from helper.transaction_type import TransactionType


class StakeHistoryReport:
    """
    Read-only DTO built from a list of STAKE_TRANSACTIONS rows.
    Supports filtering by transaction type or bet_id.
    """

    def __init__(self, gambler_id: str, session_id: str,
                 transactions: list):
        self.gambler_id   = gambler_id
        self.session_id   = session_id
        self.transactions = transactions  

        # pre-compute summary
        self.total_transactions = len(transactions)
        self.net_profit_loss    = self._calc_net()
        self.type_breakdown     = self._calc_type_breakdown()
        self.starting_balance   = (
            Decimal(str(transactions[0]["balance_before"]))
            if transactions else Decimal("0.00")
        )
        self.ending_balance     = (
            Decimal(str(transactions[-1]["balance_after"]))
            if transactions else Decimal("0.00")
        )

    def _calc_net(self) -> Decimal:
        if not self.transactions:
            return Decimal("0.00")
        return (Decimal(str(self.transactions[-1]["balance_after"])) -
                Decimal(str(self.transactions[0]["balance_before"])))

    def _calc_type_breakdown(self) -> dict:
        breakdown = {t.value: {"count": 0, "total_amount": Decimal("0.00")}
                     for t in TransactionType}
        for tx in self.transactions:
            t = tx["transaction_type"]
            if t in breakdown:
                breakdown[t]["count"]        += 1
                breakdown[t]["total_amount"] += Decimal(str(tx["amount"]))
        return breakdown

    def filter_by_type(self, transaction_type: TransactionType) -> list:
        return [tx for tx in self.transactions
                if tx["transaction_type"] == transaction_type.value]

    def filter_by_bet(self, bet_id: str) -> list:
        return [tx for tx in self.transactions if tx.get("bet_id") == bet_id]

    def summary(self) -> str:
        pnl_sign = "+" if self.net_profit_loss >= 0 else ""
        lines = [
            f"\n{'='*55}",
            f"  STAKE HISTORY REPORT",
            f"  Session  : {self.session_id}",
            f"  Gambler  : {self.gambler_id}",
            f"{'='*55}",
            f"  Starting Balance : ${self.starting_balance:,.2f}",
            f"  Ending Balance   : ${self.ending_balance:,.2f}",
            f"  Net P&L          : {pnl_sign}${self.net_profit_loss:,.2f}",
            f"  Total Transactions: {self.total_transactions}",
            f"  --",
            f"  Transaction Breakdown:",
        ]
        for tx_type, data in self.type_breakdown.items():
            if data["count"] > 0:
                lines.append(
                    f"    {tx_type:<20} count={data['count']:>3}   "
                    f"total=${data['total_amount']:,.2f}")
        lines.append(f"  --")
        lines.append(f"  Transaction Detail:")
        for tx in self.transactions:
            pnl = Decimal(str(tx["net_change"]))
            sign = "+" if pnl >= 0 else ""
            lines.append(
                f"    [{tx['created_at']}]  "
                f"{tx['transaction_type']:<20}  "
                f"amount=${Decimal(str(tx['amount'])):>10,.2f}  "
                f"balance=${Decimal(str(tx['balance_after'])):>10,.2f}  "
                f"({sign}${pnl:,.2f})"
            )
        lines.append(f"{'='*55}")
        return "\n".join(lines)