from validation.validation import InputValidator

class SafeInputHandler:

    def __init__(self, validator: InputValidator):
        self.validator = validator

    def get_decimal(self, prompt):
        while True:
            value = input(prompt)
            parsed, result = self.validator.parse_and_validate_numeric(value)

            if not result.is_valid:
                print("❌", result.errors)
                continue

            return parsed