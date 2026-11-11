from producers.news.financial_filter import (
    evaluate_financial_news
)
 
 
TEST_ARTICLES = [
 
    {
        "headline": "ICICI Direct Brokerage Charges - Equity Pricing Plan Overview",
        "description": "Explore our brokerage charges and trading services.",
        "publisher": "ICICI Direct"
    },
 
    {
        "headline": "Tata Steel shares rise 2%. Why brokerages remain bullish; see up to 30% upside potential",
        "description": "Brokerages remain bullish on Tata Steel and discuss its growth outlook.",
        "publisher": "The Economic Times"
    },
 
    {
        "headline": "Infosys reports strong quarterly revenue and profit growth",
        "description": "The company announced its quarterly financial results.",
        "publisher": "Reuters"
    },
 
    {
        "headline": "Jefferies upgrades HDFC Bank to buy and raises target price",
        "description": "The brokerage revised its target price following its latest assessment.",
        "publisher": "NDTV Profit"
    },
 
    {
        "headline": "Sponsored content: Best stocks to invest in today",
        "description": "Register now and start trading.",
        "publisher": "Example Publisher"
    },
 
    {
        "headline": "Mizoram and SBI sign agreement for digital revenue collection",
        "description": "The agreement enables digital revenue collection by village councils.",
        "publisher": "Economic Times"
    }
]
 
 
print("\n========== FINTEL FINANCIAL FILTER TEST ==========\n")
 
for article in TEST_ARTICLES:
 
    result = evaluate_financial_news(
        article["headline"],
        article["description"],
        article["publisher"]
    )
 
    print("-" * 90)
 
    print("HEADLINE :", article["headline"])
    print("PUBLISHER:", article["publisher"])
    print("ACCEPTED :", result.accepted)
    print("CATEGORY :", result.category)
    print("SCORE    :", result.score)
    print("REASON   :", result.reason)
 
print("\n========== TEST COMPLETED ==========\n")