import re
from typing import Dict, List
from app.utils.logger import get_logger
from app.config import Config
logger = get_logger("governance", "logs/governance.log")

BANNED_PHRASES = Config.BANNED_PHRASES
CONFIDENCE_THRESHOLD = Config.CONFIDENCE_THRESHOLD

# Simple regexes for crude PII detection/redaction
RE_DATE = re.compile(r'\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b')
RE_ID = re.compile(r'\b(?:id|ssn|passport|card)[\s:]*[A-Za-z0-9-]{4,}\b', re.IGNORECASE)
# Names: this is heuristic; you can replace with NER later
RE_NAME = re.compile(r'\b([A-Z][a-z]{1,20}\s[A-Z][a-z]{1,20})\b')

class GovernanceAgent:
    def __init__(self, banned_phrases=None, threshold: float = CONFIDENCE_THRESHOLD):
        self.banned_phrases = banned_phrases or BANNED_PHRASES
        self.threshold = threshold
        logger.info("GovernanceAgent initialized (threshold=%.2f)", threshold)

    def _check_banned_phrases(self, text: str) -> List[str]:
        matches = []
        lower = text.lower()
        for p in self.banned_phrases:
            if p.lower() in lower:
                matches.append(p)
        return matches

    def _redact_pii(self, text: str) -> str:
        text = RE_DATE.sub("[REDACTED_DATE]", text)
        text = RE_ID.sub("[REDACTED_ID]", text)
        # redact name-like patterns
        text = RE_NAME.sub("[REDACTED_NAME]", text)
        return text

    def evaluate(self, answer: str, trace: list, confidence: float) -> Dict:
        reasons = []
        approved = True
        if confidence is None:
            confidence = 0.0
        if confidence < self.threshold:
            approved = False
            reasons.append(f"low_confidence ({confidence:.2f} < {self.threshold})")
        banned = self._check_banned_phrases(answer)
        if banned:
            approved = False
            reasons.append(f"banned_phrases_present: {banned}")
        redacted_answer = self._redact_pii(answer)
        if redacted_answer != answer:
            reasons.append("pii_redacted")
        reason = "; ".join(reasons) if reasons else "approved"
        logger.info("Governance evaluated: approved=%s reason=%s", approved, reason)
        return {"approved": approved, "reason": reason, "redacted_answer": redacted_answer}
