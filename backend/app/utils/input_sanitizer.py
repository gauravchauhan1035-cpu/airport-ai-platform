"""Input sanitization utilities to defend against prompt injection attacks."""

import re
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    # Direct instruction override attempts
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?|context)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?)", re.IGNORECASE),
    # System prompt / internals extraction
    re.compile(r"(show|reveal|display|print|output|repeat|echo)\s+(me\s+)?(your|the|system)\s+(prompt|instructions?|rules?|context)", re.IGNORECASE),
    re.compile(r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?|hidden)", re.IGNORECASE),
    # Chain-of-thought / internal reasoning extraction
    re.compile(r"(reveal|show|explain|describe|tell\s+me)\s+(your\s+)?(chain.of.thought|reasoning|thought\s+process|internal\s+logic|decision\s+process)", re.IGNORECASE),
    re.compile(r"how\s+do\s+you\s+(work|decide|think|process|route|determine)", re.IGNORECASE),
    re.compile(r"(what|show)\s+(is|are)\s+your\s+(internal|hidden|secret|underlying)", re.IGNORECASE),
    re.compile(r"walk\s+me\s+through\s+your\s+(thinking|reasoning|logic|process)", re.IGNORECASE),
    # Role play / persona override
    re.compile(r"you\s+are\s+now\s+(a|an|the)\s+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a|an|if)\s+", re.IGNORECASE),
    re.compile(r"pretend\s+(to\s+be|you\s+are)\s+", re.IGNORECASE),
    # Technical exploitation
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\]", re.IGNORECASE),
    re.compile(r"\[\s*SYSTEM\s*\]", re.IGNORECASE),
    re.compile(r"<<\s*SYS\s*>>", re.IGNORECASE),
]

# SQL-specific dangerous patterns in user questions
_SQL_DANGEROUS_PATTERNS = [
    # Bulk data / table enumeration attempts
    re.compile(r"\b(show|list|display|give|dump|export)\b.*\b(all|every|entire|complete|full)\b.*\b(data|records?|rows?|tables?|columns?|schema|database|entries)\b", re.IGNORECASE),
    re.compile(r"\b(show|list|display|describe|explain)\b.*\b(schema|structure|tables?|columns?|DDL|metadata)\b", re.IGNORECASE),
    re.compile(r"\b(dump|export|download)\b.*\b(database|table|data)\b", re.IGNORECASE),
    # Catch 'list every table', 'list all tables', 'show tables' standalone patterns
    re.compile(r"\b(list|show|display|get)\b.{0,20}\b(every|all|the)\b.{0,10}\btables?\b", re.IGNORECASE),
    re.compile(r"\b(what|which)\s+tables?\s+(are|exist|do\s+you\s+have)", re.IGNORECASE),
    # Schema / database structure
    re.compile(r"\b(show|get|display|reveal)\s+(the\s+)?\b(database\s+schema|table\s+schema|db\s+schema)", re.IGNORECASE),
    re.compile(r"\bsqlite_master\b", re.IGNORECASE),
    re.compile(r"\bpragma\b", re.IGNORECASE),
    re.compile(r"\binformation_schema\b", re.IGNORECASE),
]


def sanitize_user_input(user_input: str) -> str:
    """Sanitize user input to remove prompt injection markers.
    
    This does NOT reject the input — it strips known injection delimiters
    so that the remaining text is safe to embed in prompts.
    """
    # Strip null bytes
    cleaned = user_input.replace("\x00", "")
    
    # Strip common injection delimiters
    cleaned = re.sub(r"<\s*/?\s*system\s*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[\s*/?\s*INST\s*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[\s*/?\s*SYSTEM\s*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<<\s*/?\s*SYS\s*>>", "", cleaned, flags=re.IGNORECASE)
    
    # Collapse excessive whitespace
    cleaned = re.sub(r"\s{3,}", "  ", cleaned).strip()
    
    return cleaned


def detect_prompt_injection(user_input: str) -> bool:
    """Return True if the input looks like a prompt injection attempt."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(user_input):
            logger.warning("Prompt injection attempt detected: %s", user_input[:100])
            return True
    return False


def detect_data_exfiltration(user_input: str) -> bool:
    """Return True if the input is attempting to dump/enumerate the database."""
    for pattern in _SQL_DANGEROUS_PATTERNS:
        if pattern.search(user_input):
            logger.warning("Data exfiltration attempt detected: %s", user_input[:100])
            return True
    return False
