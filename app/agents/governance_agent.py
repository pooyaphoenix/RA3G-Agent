import re
from typing import Dict, List, Optional

from app.utils.logger import get_logger
from app.config import Config

logger = get_logger("governance", "logs/governance.log")

BANNED_PHRASES = getattr(Config, "BANNED_PHRASES", [])
CONFIDENCE_THRESHOLD = getattr(Config, "CONFIDENCE_THRESHOLD", 0.5)
THRESHOLDS = getattr(Config, "THRESHOLDS", {})
# Simple regexes for crude PII detection/redaction
RE_DATE = re.compile(r'\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b')
RE_ID = re.compile(r'\b(?:id|ssn|passport|card)[\s:]*[A-Za-z0-9-]{4,}\b', re.IGNORECASE)
# Names: this is heuristic; you can replace with NER later
RE_NAME = re.compile(r'\b([A-Z][a-z]{1,20}\s[A-Z][a-z]{1,20})\b')
# Email pattern: user@domain.com
RE_EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
# Phone pattern: supports various formats (US: (123) 456-7890, 123-456-7890, 123.456.7890, international: +1-123-456-7890)
# Matches phone numbers with optional country code, parentheses, and various separators
RE_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")
# IP address pattern: IPv4 addresses
RE_IP = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

class GovernanceAgent:
    def __init__(
        self,
        banned_phrases=None,
        threshold: Optional[float] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ):
        self.banned_phrases = banned_phrases or BANNED_PHRASES
        self.thresholds = dict(THRESHOLDS or {})

        if thresholds:
            self.thresholds.update(thresholds)
        if threshold is not None:
            # Backwards compatibility for existing single-threshold usage
            self.thresholds["reasoner"] = threshold

        self.reasoner_threshold = self.thresholds.get("reasoner", CONFIDENCE_THRESHOLD)
        self.retriever_threshold = self.thresholds.get("retriever")

        logger.info(
            "GovernanceAgent initialized (reasoner_threshold=%.2f, retriever_threshold=%s)",
            self.reasoner_threshold,
            f"{self.retriever_threshold:.2f}" if self.retriever_threshold is not None else "None",
        )

    def _check_banned_phrases(self, text: str) -> List[str]:
        matches = []
        lower = text.lower()
        for p in self.banned_phrases:
            if p.lower() in lower:
                matches.append(p)
        return matches

    def _redact_pii(self, text: str) -> str:
        original_text = text
        
        # Track redactions for logging
        redactions = []
        
        # Redact emails
        email_matches = RE_EMAIL.findall(text)
        if email_matches:
            text = RE_EMAIL.sub("[REDACTED_EMAIL]", text)
            redactions.append(f"email(s): {len(email_matches)}")
            logger.info("Redacted %d email(s) from text", len(email_matches))
        
        # Redact phone numbers
        phone_matches = RE_PHONE.findall(text)
        if phone_matches:
            text = RE_PHONE.sub("[REDACTED_PHONE]", text)
            redactions.append(f"phone(s): {len(phone_matches)}")
            logger.info("Redacted %d phone number(s) from text", len(phone_matches))
        
        # Redact IP addresses
        ip_matches = RE_IP.findall(text)
        # Filter out false positives (like years 1920, 2024, etc.)
        valid_ips = [ip for ip in ip_matches if self._is_valid_ip(ip)]
        if valid_ips:
            for ip in valid_ips:
                text = text.replace(ip, "[REDACTED_IP]")
            redactions.append(f"IP address(es): {len(valid_ips)}")
            logger.info("Redacted %d IP address(es) from text", len(valid_ips))
        
        # Redact dates
        date_matches = RE_DATE.findall(text)
        if date_matches:
            text = RE_DATE.sub("[REDACTED_DATE]", text)
            redactions.append(f"date(s): {len(date_matches)}")
        
        # Redact IDs
        id_matches = RE_ID.findall(text)
        if id_matches:
            text = RE_ID.sub("[REDACTED_ID]", text)
            redactions.append(f"ID(s): {len(id_matches)}")
        
        # Redact names
        name_matches = RE_NAME.findall(text)
        if name_matches:
            text = RE_NAME.sub("[REDACTED_NAME]", text)
            redactions.append(f"name(s): {len(name_matches)}")
        
        if redactions and text != original_text:
            logger.info("PII redaction summary: %s", ", ".join(redactions))
        
        return text
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """Validate if a string is a valid IP address."""
        parts = ip_str.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def evaluate(
        self,
        answer: str,
        trace: list,
        confidence: float,
        retriever_confidence: Optional[float] = None,
    ) -> Dict:
        reasons = []
        approved = True
        if confidence is None:
            confidence = 0.0
        if confidence < self.reasoner_threshold:
            approved = False
            reasons.append(
                f"reasoner_low_confidence ({confidence:.2f} < {self.reasoner_threshold})"
            )

        if (
            retriever_confidence is not None
            and self.retriever_threshold is not None
            and retriever_confidence < self.retriever_threshold
        ):
            approved = False
            reasons.append(
                f"retriever_low_confidence ({retriever_confidence:.2f} < {self.retriever_threshold})"
            )

        banned = self._check_banned_phrases(answer)
        if banned:
            approved = False
            reasons.append(f"banned_phrases_present: {banned}")
        redacted_answer = self._redact_pii(answer)
        if redacted_answer != answer:
            reasons.append("pii_redacted")
        reason = "; ".join(reasons) if reasons else "approved"
        logger.info(
            "Governance evaluated: approved=%s reason=%s (thresholds=%s)",
            approved,
            reason,
            {
                "reasoner": self.reasoner_threshold,
                "retriever": self.retriever_threshold,
            },
        )
        return {"approved": approved, "reason": reason, "redacted_answer": redacted_answer}
