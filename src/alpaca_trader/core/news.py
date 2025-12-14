from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from textblob import TextBlob
from alpaca_trader.models.asset import Asset
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

class NewsArticle(BaseModel):
    """Normalized News Article Model."""
    id: str
    headline: str
    symbol: str
    source: str
    url: Optional[str] = None
    created_at: datetime
    summary: Optional[str] = None
    sentiment_score: float = 0.0

    @property
    def is_fresh(self) -> bool:
        """Check if article is younger than 24 hours."""
        # Note: In production, ensure Timezones are handled (UTC)
        # Assuming created_at is aware or we compare carefully.
        cutoff = datetime.now(self.created_at.tzinfo) - timedelta(hours=24)
        return self.created_at >= cutoff

class NewsEngine:
    """
    Handles fetching news, analyzing sentiment, and filtering for 'Material Events'.
    """

    # Valid Topics Strings (Simple Keyword Matching for MVP)
    ALLOWED_KEYWORDS = [
        # Earnings
        r"earnings", r"eps", r"revenue", r"beat", r"miss", r"guidance", r"report", 
        # M&A
        r"merger", r"acquisition", r"buyout", r"stake",
        # Biotech / Federal
        r"fda", r"approval", r"clearance", r"phase", 
        # Business
        r"contract", r"partnership", r"agreement", r"awarded",
        # Insiders
        r"form 4", r"insider"
    ]

    BANNED_KEYWORDS = [
        r"top 10", r"stocks to watch", r"analysis", r"opinion", 
        r"why (.*) is moving", r"upgrade", r"downgrade", r"rating"
    ]

    def __init__(self):
        self._cache_seen_headlines: Dict[str, datetime] = {}

    def process_article(self, article: NewsArticle) -> Optional[NewsArticle]:
        """
        Main Pipeline:
        1. Check Freshness.
        2. Deduplicate.
        3. Filter (Allow/Ban lists).
        4. Analyze Sentiment.
        """
        
        # 1. Freshness
        if not article.is_fresh:
            logger.debug("News dropped: Too old", id=article.id)
            return None

        # 2. Deduplication (Exact headline match within 48h window)
        # Note: Ideally usage of fuzz or checking ID.
        if article.headline in self._cache_seen_headlines:
            logger.debug("News dropped: Duplicate", headline=article.headline)
            return None
        self._cache_seen_headlines[article.headline] = datetime.now()

        # 3. Content Filters
        text_body = f"{article.headline} {article.summary or ''}".lower()
        
        if self._is_banned(text_body):
            logger.debug("News dropped: Banned Content", headline=article.headline)
            return None
            
        if not self._is_material(text_body):
            logger.debug("News dropped: Not Material", headline=article.headline)
            return None

        # 4. Sentiment Analysis
        # Using simple TextBlob for MVP. 
        # Polarity: -1.0 (Negative) to 1.0 (Positive)
        blob = TextBlob(text_body)
        sentiment = blob.sentiment.polarity
        
        article.sentiment_score = sentiment
        
        if sentiment < 0.2: # Simple threshold, can tune later
            logger.debug("News dropped: Low Sentiment", score=sentiment)
            return None

        return article

    def _is_material(self, text: str) -> bool:
        """Check if text contains any allowed keywords."""
        text = text.lower()
        for pattern in self.ALLOWED_KEYWORDS:
            if re.search(pattern, text):
                return True
        return False

    def _is_banned(self, text: str) -> bool:
        """Check if text contains any banned keywords."""
        text = text.lower()
        for pattern in self.BANNED_KEYWORDS:
            if re.search(pattern, text):
                return True
        return False
