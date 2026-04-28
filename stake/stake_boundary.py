from decimal import Decimal


class StakeBoundary:
    LOWER_WARNING_RATIO = Decimal("0.20")   
    UPPER_WARNING_RATIO = Decimal("0.80")   

    def __init__(self, lower_limit: Decimal, upper_limit: Decimal,
                 lower_warning_ratio: Decimal = None,
                 upper_warning_ratio: Decimal = None):

        if lower_limit <= 0:
            raise ValueError("Lower limit must be positive")
        if upper_limit <= lower_limit:
            raise ValueError("Upper limit must be greater than lower limit")

        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.range       = upper_limit - lower_limit

        self.lower_warning_ratio = lower_warning_ratio or self.LOWER_WARNING_RATIO
        self.upper_warning_ratio = upper_warning_ratio or self.UPPER_WARNING_RATIO

        # absolute warning thresholds
        self.lower_warning_threshold = lower_limit + (self.range * self.lower_warning_ratio)
        self.upper_warning_threshold = lower_limit + (self.range * self.upper_warning_ratio)

    def is_within_bounds(self, stake: Decimal) -> bool:
        return self.lower_limit <= stake <= self.upper_limit

    def is_below_lower(self, stake: Decimal) -> bool:
        return stake < self.lower_limit

    def is_above_upper(self, stake: Decimal) -> bool:
        return stake > self.upper_limit

    def is_in_lower_warning_zone(self, stake: Decimal) -> bool:
        return self.lower_limit <= stake <= self.lower_warning_threshold

    def is_in_upper_warning_zone(self, stake: Decimal) -> bool:
        return self.upper_warning_threshold <= stake <= self.upper_limit

    def validate(self, stake: Decimal) -> dict:
        
        warnings = []
        errors   = []

        if self.is_below_lower(stake):
            errors.append(
                f"Stake {stake} is below lower limit ${self.lower_limit}")
        elif self.is_in_lower_warning_zone(stake):
            warnings.append(
                f"Stake ${stake} is approaching lower limit ${self.lower_limit} "
                f"(warning threshold: ${self.lower_warning_threshold})")

        if self.is_above_upper(stake):
            errors.append(
                f"Stake ${stake} exceeds upper limit ${self.upper_limit}")
        elif self.is_in_upper_warning_zone(stake):
            warnings.append(
                f"Stake ${stake} is approaching upper limit ${self.upper_limit} "
                f"(warning threshold: ${self.upper_warning_threshold})")

        return {
            "stake":      stake,
            "is_valid":   len(errors) == 0,
            "warnings":   warnings,
            "errors":     errors,
            "lower_limit": self.lower_limit,
            "upper_limit": self.upper_limit,
        }