class ValidationError(Exception):
    pass


class RequestValidator:
    def __init__(self, fields: dict):
        self.fields = fields

    def validate(self, data: dict) -> dict:
        validated = {}
        for field_name, rules in self.fields.items():
            # Check if field is required and present
            if rules.get("required", False) and field_name not in data:
                raise ValidationError(f"Missing required field: {field_name}")

            if field_name in data:
                value = data[field_name]

                # Type validation
                if "type" in rules and not isinstance(value, rules["type"]):
                    raise ValidationError(f"Invalid type for field {field_name}")

                # Length validation for strings
                if isinstance(value, str):
                    min_length = rules.get("min_length")
                    if min_length and len(value) < min_length:
                        raise ValidationError(f"Field {field_name} must be at least {min_length} characters long")

                validated[field_name] = value

        return validated
