from producers.news.company_filter import (
    find_matching_companies,
    is_relevant_article
)
 
 
def test_relevant_articles():
    matches = find_matching_companies(
        "Reliance Industries shares rise after strong Q2 results"
    )
 
    assert "RELIANCE" in matches
    assert is_relevant_article(
        "Infosys announces quarterly results"
    )
 
    print("Relevant article tests passed!")
 
 
def test_unrelated_articles():
    matches = find_matching_companies(
        "India wins the cricket match against Australia"
    )
 
    assert matches == []
    assert not is_relevant_article(
        "India wins the cricket match against Australia"
    )
 
    print("Unrelated article tests passed!")
 
 
def test_multiple_companies():
    matches = find_matching_companies(
        "Reliance Industries and HDFC Bank shares rise"
    )
 
    assert "RELIANCE" in matches
    assert "HDFCBANK" in matches
 
    print("Multiple company detection test passed!")
 
 
if __name__ == "__main__":
    test_relevant_articles()
    test_unrelated_articles()
    test_multiple_companies()