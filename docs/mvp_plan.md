# News Sentiment Momentum MVP Plan

## 🎯 Objective
Automated trading system targeting **Small-Mid Cap ($300M-$2B)** stocks priced **$2-$20**. The system executes long positions triggered by **Material News Events**, managed by a strict, multi-stage exit strategy to maximize momentum capture and minimize bag-holding.

## 1. 🔍 Universe Selection (The Filter)
*Frequency: Daily (Pre-market) & Intraday updates*

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| **Price** | $2.00 - $20.00 | High percentage volatility. |
| **Market Cap** | $300M - $2B | "Sweet spot" where news moves price fast, but liquidity exists. |
| **Liquidity** | Volume > 500k (Avg) | Avoid slippage traps. |

## 2. 📰 News Signal Engine
*Source: Alpaca News API (Benzinga)*

### A. Content Filters (The "Material Only" Gate)
The system **ONLY** triggers on these specific topics. All others are discarded.

1.  **Earnings**: `EPS`, `Revenue`, `Beat`, `Miss`, `Guidance`
2.  **M&A**: `Merger`, `Acquisition`, `Buyout`, `Stake`
3.  **Biotech/Regs**: `FDA`, `Approval`, `Unknown Phase`, `Clearance`
4.  **Business**: `Contract`, `Partnership`, `Agreement`, `Awarded`
5.  **Insiders**: `Form 4`, `Director purchase`, `Insider buy`

### B. The "Ignore List" (Noise Filter)
Discard if headline contains:
- "Top 10", "Stocks to watch", "Analysis", "Opinion", "Why [Ticker] is moving"
- Analyst Ratings (Upgrades/Downgrades) - *Too lagging.*

### C. Validation Logic
1.  **Freshness Check**:
    - **Ideal**: < 12 hours.
    - **Hard Limit**: < 24 hours. (Reject if older).
2.  **Deduplication**:
    - Calculate Token Set Ratio (fuzzy matching).
    - Reject if > 80% similar to an article processed for this ticker in the last 48h.
3.  **Sentiment Score**:
    - Use Model: `ProsusAI/finbert` (Hugging Face) or Dictionary-based.
    - **Trigger**: Sentiment > Positive Threshold (e.g., 0.65 probability).

## 3. 🛡️ Risk & Execution Logic (The Manager)

### A. Entry
- **Condition**: Valid Material News + Price is trending UP (e.g., above VWAP or moving average).
- **Action**: Market Buy.

### B. The "Safety Nets" (Defense)
1.  **Hard Stop-Loss**: Sell **100%** at Entry Price - **5%** (Avg of 4-6%).
2.  **The "Stale" Timer**:
    - Start timer on fill.
    - **Check at T+45 mins**: Is Profit > **1.5%**?
    - **NO**: Sell **100%** immediately (Dead money).
    - **YES**: Continue holding.

### C. Profit Taking (Offense)
1.  **Target 1 (The Bank)**:
    - Condition: Price >= Entry + **6.5%** (Avg of 5-8%).
    - Action: Sell **50%** of position.
2.  **The Runner (Moon Bag)**:
    - Remaining 50%.
    - Logic: **Trailing Stop** of **3%** from the *Highest High* since entry.
    - *Let it run until it pulls back.*

### D. Emergency Eject Buttons
*Higher priority than Trailing Stop.*

1.  **RSI Overheat**:
    - Indicator: RSI (14) on 5-min timeframe.
    - Trigger: RSI > **85**.
    - Action: Sell **100%**.
2.  **Volume Exhaustion**:
    - Condition: Price = `New High`, BUT Volume < `Previous Candle Volume` (Divergence).
    - Action: Sell **100%**.
3.  **Sentiment Flip**:
    - Condition: New article detected with **Negative** sentiment.
    - Action: Sell **100%**.

## 4. 🏗️ Tech Implementation Plan

### Phase 1: Data & Screening
- [ ] Implement `AlpacaClient` wrapper.
- [ ] Build `MarketScreener` to fetch $2-$20, $300M-$2B tickers.

### Phase 2: News Processor
- [ ] Build `NewsListener` (WebSocket).
- [ ] Implement Keyword/Regex filters for "Allowed/Banned".
- [ ] Implement `DedupService` (using `thefuzz` or similar).

### Phase 3: Strategy Loop
- [ ] Create `PositionManager` class.
- [ ] Implement the `45_min_timer` async task.
- [ ] Implement `TechnicalMonitor` (RSI/Volume calc).

### Phase 4: Integration
- [ ] Paper Trading validation.
- [ ] Logging & Alerts.

## 5. Dependencies
- `alpaca-py`: API connection.
- `pandas-ta`: Technical indicators (RSI).
- `torch` & `transformers`: For FinBERT (optional, can start with `nltk`/`TextBlob` for MVP).
- `thefuzz`: String matching for deduplication.
