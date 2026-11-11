import re
import html
 
from dataclasses import dataclass
from typing import Optional
 
 
# ============================================================
# TEXT CLEANING
# ============================================================
 
def clean_text(value: Optional[str]) -> str:
    """Remove HTML tags and normalize text."""
 
    if not value:
        return ""
 
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
 
    return value.strip()
 
 
# ============================================================
# EXPLICIT PROMOTIONAL / ADVERTISEMENT PATTERNS
# ============================================================
 
PROMOTIONAL_PATTERNS = [
    r"\bsponsored content\b",
    r"\bpaid promotion\b",
    r"\bpromoted content\b",
    r"\badvertisement\b",
    r"\badvertorial\b",
    r"\bpartner content\b",
    r"\bbrand promotion\b",
    r"\bopen a demat account\b",
    r"\bopen trading account\b",
    r"\bdownload our trading app\b",
    r"\bregister now\b",
    r"\bsign up now\b",
    r"\bsubscribe now\b",
    r"\bclick here to invest\b",
    r"\bstart trading today\b",
    r"\bget started with our platform\b",
    r"\bbrokerage charges\b",
    r"\bpricing plan overview\b",
    r"\baccount opening offer\b",
    r"\bexclusive offer\b"
]
 
 
# ============================================================
# FINANCIAL NEWS CATEGORIES
# ============================================================
 
FINANCIAL_CATEGORIES = {
 
    "financial_performance": [
        "quarterly results",
        "financial results",
        "annual results",
        "quarterly earnings",
        "annual earnings",
        "revenue growth",
        "revenue declined",
        "revenue increased",
        "revenue rose",
        "revenue fell",
        "net profit",
        "net loss",
        "operating profit",
        "operating margin",
        "ebitda",
        "cash flow",
        "debt",
        "profit growth",
        "profit decline",
        "earnings growth",
        "earnings decline"
    ],
 
    "business_developments": [
        "major contract",
        "order win",
        "new project",
        "business expansion",
        "capacity expansion",
        "new investment",
        "capital expenditure",
        "capex",
        "acquisition",
        "merger",
        "partnership",
        "strategic agreement",
        "joint venture",
        "production increase",
        "production shutdown",
        "market share",
        "new facility",
        "agreement ",
        "sign agreement",
        "digital revenue collection",
        "strategic agreement"
    ],
 
    "corporate_actions": [
        "dividend",
        "share buyback",
        "buyback",
        "bonus shares",
        "stock split",
        "rights issue",
        "fundraising",
        "fund raising",
        "qualified institutional placement",
        "qip",
        "demerger",
        "share allotment"
    ],
 
    "regulatory_legal": [
        "regulatory action",
        "regulatory approval",
        "sebi",
        "rbi",
        "penalty",
        "investigation",
        "court ruling",
        "legal dispute",
        "tax dispute",
        "compliance",
        "gstat",
        "government approval",
        "show cause notice"
    ],
 
    "analyst_recommendations": [
        "analyst recommendation",
        "brokerage recommendation",
        "brokerages remain bullish",
        "brokerage remains bullish",
        "brokerage upgrade",
        "brokerage downgrade",
        "upgraded to buy",
        "downgraded to sell",
        "buy rating",
        "sell rating",
        "hold rating",
        "target price",
        "price target",
        "revised target",
        "analyst rating",
        "jefferies",
        "morgan stanley",
        "goldman sachs",
        "morgan stanley",
        "institutional investors",
        "fpi investment",
        "fii investment"
    ],
 
    "stock_market_commentary": [
        "shares rise",
        "shares fall",
        "stock rises",
        "stock falls",
        "share price",
        "stock price",
        "market valuation",
        "market capitalization",
        "market capitalisation",
        "bullish outlook",
        "bearish outlook",
        "trading volume",
        "52 week high",
        "52-week high",
        "52 week low",
        "52-week low",
        "outperforms the market",
        "underperforms the market",
        "stock rally",
        "stock correction",
        "investor sentiment"
    ],
 
    "sector_developments": [
        "sector outlook",
        "industry outlook",
        "industry regulation",
        "sector regulation",
        "tariff changes",
        "commodity prices",
        "interest rate changes",
        "policy changes",
        "import duty",
        "export duty",
        "industry demand",
        "sector demand"
    ]
}
 
 
# ============================================================
# LOW-VALUE GENERIC MARKET ROUNDUPS
# ============================================================
 
GENERIC_ROUNDUP_PATTERNS = [
    r"\bstocks? in news\b",
    r"\btop stocks? to buy today\b",
    r"\bstocks? to watch today\b",
    r"\bmarket live updates\b",
    r"\btop gainers and losers\b",
    r"\bmarket movers today\b",
    r"\bpre-market updates\b",
    r"\bclosing bell updates\b"
]
 
 
# ============================================================
# FINANCIAL NEWS FILTER
# ============================================================
 
@dataclass
class FinancialNewsResult:
    accepted: bool
    category: str
    score: int
    reason: str
 
 
def contains_pattern(text, patterns):
    """Check whether any regular expression matches."""
 
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )
 
 
def find_financial_categories(text):
    """Identify financial news categories."""
 
    matched_categories = []
 
    for category, keywords in FINANCIAL_CATEGORIES.items():
 
        if any(
            keyword.lower() in text
            for keyword in keywords
        ):
            matched_categories.append(category)
 
    return matched_categories
 
 
def evaluate_financial_news(
    headline,
    description="",
    publisher=""
):
    """
    Evaluate whether an article is meaningful financial news.
 
    Company relevance must be checked separately using
    company_filter.py.
 
    Returns a FinancialNewsResult.
    """
 
    headline = clean_text(headline)
    description = clean_text(description)
    publisher = clean_text(publisher)
 
    headline_lower = headline.lower()
    description_lower = description.lower()
 
    combined_text = (
        f"{headline_lower} {description_lower}"
    )
 
    # --------------------------------------------------------
    # 1. Reject explicit promotional content
    # --------------------------------------------------------
 
    if contains_pattern(
        headline_lower,
        PROMOTIONAL_PATTERNS
    ):
 
        return FinancialNewsResult(
            accepted=False,
            category="promotional",
            score=0,
            reason="Promotional or advertisement-style headline"
        )
 
    if contains_pattern(
        description_lower,
        PROMOTIONAL_PATTERNS
    ):
 
        return FinancialNewsResult(
            accepted=False,
            category="promotional",
            score=0,
            reason="Promotional or advertisement-style description"
        )
 
    # --------------------------------------------------------
    # 2. Identify financial categories
    # --------------------------------------------------------
 
    categories = find_financial_categories(
        combined_text
    )
 
    if not categories:
 
        return FinancialNewsResult(
            accepted=False,
            category="unclassified",
            score=0,
            reason="No meaningful financial news signals found"
        )
 
    # --------------------------------------------------------
    # 3. Reject generic market roundups
    # --------------------------------------------------------
 
    is_generic_roundup = contains_pattern(
        headline_lower,
        GENERIC_ROUNDUP_PATTERNS
    )
 
    has_company_specific_analysis = any(
        category in categories
        for category in [
            "financial_performance",
            "business_developments",
            "corporate_actions",
            "regulatory_legal"
        ]
    )
 
    if is_generic_roundup and not has_company_specific_analysis:
 
        return FinancialNewsResult(
            accepted=False,
            category="generic_market_roundup",
            score=0,
            reason="Generic market roundup without specific company development"
        )
 
    # --------------------------------------------------------
    # 4. Assign relevance score
    # --------------------------------------------------------
 
    score = 0
 
    category_weights = {
        "financial_performance": 5,
        "business_developments": 5,
        "corporate_actions": 5,
        "regulatory_legal": 5,
        "analyst_recommendations": 4,
        "stock_market_commentary": 3,
        "sector_developments": 2
    }
 
    for category in categories:
        score += category_weights.get(category, 0)
 
    # A meaningful company-specific financial signal is required.
    # Analyst and stock-market articles are allowed.
    if score < 2:
 
        return FinancialNewsResult(
            accepted=False,
            category=", ".join(categories),
            score=score,
            reason="Financial relevance score too low"
        )
 
    # --------------------------------------------------------
    # 5. Accept article
    # --------------------------------------------------------
 
    return FinancialNewsResult(
        accepted=True,
        category=", ".join(categories),
        score=score,
        reason="Meaningful financial news signals identified"
    )
 
 
# ============================================================
# SIMPLE PUBLIC INTERFACE
# ============================================================
 
def is_financially_relevant(
    headline,
    description="",
    publisher=""
):
    """Return True when an article passes the financial filter."""
 
    result = evaluate_financial_news(
        headline,
        description,
        publisher
    )
 
    return result.accepted