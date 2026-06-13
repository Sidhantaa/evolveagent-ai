import re

from app.models.response_models import SecretScanResult


class SecretScanner:
    patterns: list[tuple[str, re.Pattern[str]]] = [
        ("env_api_key", re.compile(r"\b(?:OPENAI|ANTHROPIC|GEMINI|MISTRAL|LINEAR)_API_KEY\s*=\s*[^\s]+", re.I)),
        ("linear_key", re.compile(r"\blin_api_[A-Za-z0-9_]+\b")),
        ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b")),
        ("github_token", re.compile(r"\bghp_[A-Za-z0-9_]{10,}\b")),
        ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)),
        ("password_assignment", re.compile(r"\bpassword\s*=\s*[^\s]+", re.I)),
        ("token_assignment", re.compile(r"\btoken\s*=\s*[^\s]+", re.I)),
    ]

    def scan(self, text: str | None) -> SecretScanResult:
        if not text:
            return SecretScanResult()
        detected_types: list[str] = []
        count = 0
        for label, pattern in self.patterns:
            matches = pattern.findall(text)
            if matches:
                detected_types.append(label)
                count += len(matches)
        if count == 0:
            return SecretScanResult()
        return SecretScanResult(
            status="redacted",
            secrets_detected=True,
            redaction_count=count,
            detected_types=detected_types,
            recommendation="Secrets were detected and redacted before agent/model use.",
        )

    def redact(self, text: str | None) -> tuple[str, SecretScanResult]:
        if not text:
            return "", SecretScanResult()
        result = self.scan(text)
        redacted = text
        if result.secrets_detected:
            for _, pattern in self.patterns:
                redacted = pattern.sub("[REDACTED_SECRET]", redacted)
        return redacted, result
