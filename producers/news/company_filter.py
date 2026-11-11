 
import re
 
from config.companies import COMPANIES
 
 
# Financial/business context for ambiguous short names
SHORT_NAME_CONTEXT = {
    "TCS": [
        "shares", "stock", "earnings", "revenue",
        "results", "quarter", "company", "services",
        "information technology", "IT services",
        "market", "profit", "investment"
    ],
    "SBI": [
        "state bank of india", "sbi bank",
        "shares", "stock", "banking",
        "earnings", "results", "market", "lending"
    ],
    "ITC": [
        "limited", "ltd", "shares", "stock",
        "hotels", "cigarettes", "FMCG",
        "earnings", "results", "market"
    ]
}
 
 
# Separate entities that must not be confused with target companies
EXCLUDED_PATTERNS = {
    "SBIN": [
        r"\bSBI\s+Life\b",
        r"\bSBI\s+General\b",
        r"\bSBI\s+Mutual\s+Fund\b"
    ]
}
 
 
def contains_alias(text, alias):
    pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None
 
 
def has_excluded_entity(text, symbol):
    patterns = EXCLUDED_PATTERNS.get(symbol, [])
 
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )
 
 
def has_short_name_context(text, alias):
    context_words = SHORT_NAME_CONTEXT.get(alias.upper())
 
    if not context_words:
        return True
 
    return any(
        contains_alias(text, word)
        for word in context_words
    )
 
 
def find_matching_companies(headline, full_text=""):
    headline = headline or ""
    full_text = full_text or ""
 
    matches = []
 
    for symbol, details in COMPANIES.items():
 
        aliases = details["aliases"]
 
        # Reject known separate entities, such as SBI Life
        if has_excluded_entity(headline, symbol):
            continue
 
        headline_match = False
        description_match = False
 
        for alias in aliases:
 
            # Check headline separately
            if contains_alias(headline, alias):
                if has_short_name_context(headline, alias):
                    headline_match = True
                    break
 
            # Check description separately
            if contains_alias(full_text, alias):
                if has_short_name_context(full_text, alias):
                    description_match = True
 
        if headline_match or description_match:
            matches.append(symbol)
 
    return matches
 
 
def is_relevant_article(headline, full_text=""):
    return bool(find_matching_companies(headline, full_text))
 