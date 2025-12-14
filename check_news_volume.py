from datetime import datetime, timedelta
from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from alpaca_trader.config.settings import settings

def check_news_volume():
    client = NewsClient(settings.alpaca_api_key, settings.alpaca_secret_key)
    
    # Check 1: Last 72 hours
    start_time = datetime.now() - timedelta(hours=72)
    print(f"Checking news since: {start_time} (Last 72h)")
    
    req = NewsRequest(
        limit=50, # Max per page
        start=start_time,
        include_content=True
    )
    
    try:
        news = client.get_news(req)
        items = []
        if hasattr(news, 'news'):
            if isinstance(news.news, dict):
                 items = list(news.news.values())
            else:
                 items = news.news
        elif isinstance(news, list):
             items = news
        elif isinstance(news, dict):
             items = news.get('news', [])
        
        print(f"Items found in last 24h: {len(items)}")
        
        sources = set()
        for item in items:
            source = item.source if hasattr(item, 'source') else item.get('source')
            sources.add(source)
            
        print(f"Unique sources found: {sources}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(f"Current Time: {datetime.now()}")
    print(f"Day of week: {datetime.now().strftime('%A')}")
    check_news_volume()
