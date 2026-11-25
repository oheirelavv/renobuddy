"""Input validation and safety checks for user queries."""

from __future__ import annotations

import re

MAX_INPUT_LENGTH = 2000

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(a|an|my)\s+",
    r"(system|developer)\s*prompt",
    r"reveal\s+(your|the)\s+(system|instructions|prompt|rules)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(a|an|if)",
    r"forget\s+(all|everything|your)\s+(instructions|rules|constraints)",
    r"override\s+(your|the|all)\s+(rules|instructions|safety)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"(what|show|print|output|tell)\s+(is|me|are)\s+(your|the)\s+(system|api|secret|internal)",
    r"api[_\s]?key",
    r"repeat\s+(the|your)\s+(system|instructions|prompt)",
]

OUT_OF_SCOPE_PATTERNS = [
    r"\b(condo|condominium|landed|private\s+property|commercial|office)\b",
    r"\b(stock|invest|crypto|bitcoin|forex)\b",
    r"\b(recipe|cook|weather|sport|movie|music)\b",
    r"\b(write\s+(me\s+)?(a\s+)?(poem|story|essay|code|script))\b",
]

HDB_RENO_KEYWORDS = [
    "hdb", "flat", "renovation", "reno", "permit", "hack", "wall",
    "floor", "bathroom", "toilet", "kitchen", "window", "door",
    "electrical", "wiring", "plumbing", "pipe", "aircon", "air-con",
    "contractor", "id ", "interior design", "bto", "resale",
    "ceiling", "awning", "shelter", "balcony", "gate", "tile",
    "approval", "bca", "hdb-registered",
]


def validate_input(text: str) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "Please enter a question about HDB renovations."

    if len(text) > MAX_INPUT_LENGTH:
        return False, f"Input is too long ({len(text)} characters). Please keep it under {MAX_INPUT_LENGTH} characters."

    lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return False, "I can only help with questions about HDB renovations in Singapore."

    return True, ""


def is_out_of_scope(text: str) -> bool:
    lower = text.lower()

    has_reno_keyword = any(kw in lower for kw in HDB_RENO_KEYWORDS)
    if has_reno_keyword:
        return False

    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, lower):
            return True

    return False


OUT_OF_SCOPE_RESPONSE = (
    "I'm designed to help with **HDB renovation questions** in Singapore — "
    "things like permits, wall hacking, bathroom works, window replacement, "
    "and finding registered contractors.\n\n"
    "Could you rephrase your question to be about HDB renovations?"
)

CONTRACTOR_DIRECTORY_URL = (
    "https://services2.hdb.gov.sg/webapp/BN31AWERRCMobile/BN31PListingContractor.jsp"
)
