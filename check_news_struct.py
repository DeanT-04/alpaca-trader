from alpaca.data.historical import NewsClient
from alpaca.data.requests import NewsRequest
from alpaca_trader.config.settings import settings
import datetime

client = NewsClient(settings.alpaca_api_key, settings.alpaca_secret_key)
req = NewsRequest(limit=1, start=datetime.datetime.now() - datetime.timedelta(days=1))
data = client.get_news(req)

print(f"Type: {type(data)}")
print(f"Dir: {dir(data)}")
try:
    print(f"Data dict: {data.data}")
except:
    print("No .data")

try:
    print(f"Data news: {data.news}")
except:
    print("No .news")

print("Iterating:")
for i, item in enumerate(data):
    print(f"Item {i} type: {type(item)}")
    print(f"Item {i} dir: {dir(item)}")
    break
