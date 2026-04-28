from enum import Enum

class TransactionType(Enum):
    INITIAL_STAKE = "INITIAL_STAKE"
    BET_PLACED    = "BET_PLACED"
    BET_WIN       = "BET_WIN"
    BET_LOSS      = "BET_LOSS"
    DEPOSIT       = "DEPOSIT"
    WITHDRAWAL    = "WITHDRAWAL"
    ADJUSTMENT    = "ADJUSTMENT"
    RESET         = "RESET"