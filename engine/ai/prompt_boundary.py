class PromptBoundary:
    def __init__(self):
        self.forbidden_patterns = [
            "DROP TABLE",
            "DELETE FROM",
            "INSERT INTO",
            "UPDATE",
            "ALTER TABLE",
            "CREATE TABLE",
            "shutdown",
            "reboot",
            "sudo",
            "rm -rf",
            "chmod 777",
            "eval(",
            "exec(",
            "system(",
        ]

    def validate(self, prompt: str) -> bool:
        for pattern in self.forbidden_patterns:
            if pattern.lower() in prompt.lower():
                return False
        return True

    def sanitize(self, prompt: str) -> str:
        for pattern in self.forbidden_patterns:
            prompt = prompt.replace(pattern, "[REDACTED]")
        return prompt
