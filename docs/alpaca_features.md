# 🦙 Alpaca API Features

Overview of the capabilities provided by Alpaca Markets for algorithmic trading.

## ⚡ Core Trading Features

| Feature | Description |
| :--- | :--- |
| **Commission-Free** | Trade US stocks, ETFs, and Options with $0 commission. |
| **Paper Trading** | Realistic simulation environment to test algorithms safely. |
| **Fractional Shares** | Buy/Sell equity portions for as little as **$1**. |
| **Cross-Platform** | Robust HTTP REST API and Real-time WebSocket streams. |
| **24/7 Crypto** | Trade 20+ cryptocurrencies (BTC, ETH, etc.) round the clock. |

## 🛠️ Order Types & Execution

- **Standard**: Market, Limit, Stop, Stop Limit.
- **Advanced** (Stocks only): 
  - **Bracket Orders**: Take-Profit and Stop-Loss attached to entry.
  - **Trailing Stop**: Dynamic stop that follows price movement.
  - **OTO / OCO**: One-Triggers-Other / One-Cancels-Other.
- **Time-in-Force**: Day, GTC (Good Till Canceled), OPG (At the Open), CLS (At the Close), IOC (Immediate or Cancel), FOK (Fill or Kill).
- **Extended Hours**: Full access to Pre-market (4:00am ET) and After-hours (until 8:00pm ET).

## 📊 Market Data API (v2)

### Equities
- real-time data via WebSockets (SIP & IEX feeds).
- extensive historical data (Trades, Quotes, Bars).
- Corporate actions and dividends.

### Options
- Real-time order book and trade data.
- Historical trade and bar data, including expired contracts.
- **Level 3** trading permissions (Spreads, etc.).

### News API
- **Source**: Benzinga.
- **Live**: Real-time streaming news via WebSocket.
- **Historical**: Archive back to 2015 (~130 articles/day).
- **Metadata**: Sentiment-ready data with tickers, summary, and images.

## 💰 Margin & Risk
- **Buying Power**: Up to **4x** Intraday, **2x** Overnight.
- **Short Selling**: Easy-to-borrow list available via API.
- **Pattern Day Trader (PDT)**: Protection checks and feedback.

## 📦 SDK Support
- **Python**: `alpaca-py` (Official)
- **JavaScript**: `alpaca-trade-api-js`
- **C# / .NET**: `Alpaca.Markets`
- **Go**: `alpaca-trade-api-go`
