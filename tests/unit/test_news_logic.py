import pytest
from datetime import datetime, timedelta
from alpaca_trader.core.news import NewsEngine, NewsArticle

@pytest.fixture
def engine():
    return NewsEngine()

def test_material_news_filter(engine):
    """Test that only material news triggers."""
    
    # Material
    assert engine._is_material("ABC Reports Q3 Earnings Beat")
    assert engine._is_material("FDA Approves New Drug")
    assert engine._is_material("Merger Agreement Signed")
    
    # Not Material
    assert not engine._is_material("Stock is moving up today")
    assert not engine._is_material("CEO eats a sandwich")

def test_banned_content(engine):
    """Test that banned content is filtered."""
    assert engine._is_banned("Top 10 Stocks to Watch")
    assert engine._is_banned("Why AAPL is moving")
    assert engine._is_banned("Analyst Upgrade for TSLA")

def test_sentiment_scoring(engine):
    """Test sentiment thresholding."""
    current_time = datetime.now()
    
    # Positive Article
    article = NewsArticle(
        id="1", headline="Amazing Earnings Beat expectations", symbol="TEST", 
        source="Benzinga", created_at=current_time, summary="Profits up 100%"
    )
    result = engine.process_article(article)
    assert result is not None
    assert result.sentiment_score > 0.2

    # Negative Article
    article_bad = NewsArticle(
        id="2", headline="Disastrous Crash, Bankruptcy filed", symbol="TEST", 
        source="Benzinga", created_at=current_time, summary="Everything is lost"
    )
    result_bad = engine.process_article(article_bad)
    # Should be dropped due to low sentiment
    assert result_bad is None

def test_deduplication(engine):
    """Test matching headlines are dropped."""
    current_time = datetime.now()
    article = NewsArticle(
        id="1", headline="Generic Earnings Beat Excellent Results", symbol="TEST", 
        source="Benzinga", created_at=current_time
    )
    
    # First pass: Accepted
    assert engine.process_article(article) is not None
    
    # Second pass: Rejected (Duplicate)
    assert engine.process_article(article) is None
