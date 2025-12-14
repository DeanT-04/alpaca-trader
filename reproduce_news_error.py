import os
import sys
from datetime import datetime, timedelta
# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from alpaca_trader.config.settings import settings

def test_news():
    print("Initializing NewsClient...")
    client = NewsClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key
    )
    
    print("Creating NewsRequest...")
    req = NewsRequest(
        limit=10,
        start=datetime.now() - timedelta(days=1),
        include_content=False
    )
    
    print("Fetching news...")
    try:
        data = client.get_news(req)
        print("Success!")
        print(f"Data type: {type(data)}")
        print(f"Dir data: {dir(data)}")
        
        if hasattr(data, 'news'):
            print(f"Data.news type: {type(data.news)}")
        if hasattr(data, 'data'):
            print(f"Data.data type: {type(data.data)}")
            
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news()
