from enum import Enum

class SessionStatus(Enum):
    INITIALIZED = "INITIALIZED"
    ACTIVE      = "ACTIVE"
    PAUSED      = "PAUSED"
    ENDED_WIN   = "ENDED_WIN"
    ENDED_LOSS  = "ENDED_LOSS"
    ENDED_MANUAL   = "ENDED_MANUAL"   
    ENDED_TIMEOUT  = "ENDED_TIMEOUT" 

class SessionEndReason(Enum):
    UPPER_LIMIT = "UPPER_LIMIT"
    LOWER_LIMIT = "LOWER_LIMIT"
    MANUAL      = "MANUAL"
    TIMEOUT     = "TIMEOUT"
    MAX_GAMES   = "MAX_GAMES"       
    