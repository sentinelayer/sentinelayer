import re


class OutputValidation:
    def __init__(self):
        self.allowed_patterns = [
            r'^[a-zA-Z0-9\s\.,!?\-:;"\'\(\)\[\]]+$',
        ]
        self.forbidden_patterns = [
            r'(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s+(TABLE|DATABASE|SCHEMA)',
            r'(shutdown|reboot|sudo|rm -rf|chmod 777)',
            r'(eval|exec|system)\s*\(',
        ]

    def validate(self, output: str) -> bool:
        for pattern in self.forbidden_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return False
        return True

    def validate_with_allowed(self, output: str) -> bool:
        if not self.validate(output):
            return False
        if len(output) > 5000:
            return False
        return True

    def sanitize(self, output: str) -> str:
        for pattern in self.forbidden_patterns:
            output = re.sub(pattern, "[REDACTED]", output, flags=re.IGNORECASE)
        return output[:5000]
