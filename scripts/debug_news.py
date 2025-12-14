from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from alpaca_trader.config.settings import settings
import structlog

logger = structlog.get_logger()

def inspect_news_response():
    client = NewsClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key
    )
    
    req = NewsRequest(
        limit=5,
        include_content=False
    )
    
    print("Fetching news...")
    data = client.get_news(req)
    
    print(f"Type of data: {type(data)}")
    print(f"Dir of data: {dir(data)}")
    
    if hasattr(data, 'news'):
        print(f"data.news type: {type(data.news)}")
    
    try:
        iterator = iter(data)
        print("Data is iterable.")
        first_item = next(iterator)
        print(f"First item type: {type(first_item)}")
        print(f"First item content: {first_item}")
        
    except TypeError:
        print("Data is NOT iterable.")
    except StopIteration:
        print("Data is iterable but empty.")

if __name__ == "__main__":
    inspect_news_response()
