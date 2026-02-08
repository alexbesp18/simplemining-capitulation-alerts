# SimpleMining Capitulation Alert Bot

## Overview
Python bot that monitors SimpleMining.io miner marketplace for extreme bargain deals on new-gen Bitcoin miners (S21 class). Sends Telegram alerts when high-quality listings (<=17.5 J/TH) appear at >=60% discount from last trade price (or 90-day average as fallback). Revenue/cost/ROI computed locally from hashprice.

## Commands
```bash
# Local run (dry-run without Telegram creds)
python -m src.main

# With Telegram
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python -m src.main
```

## Architecture
```
src/
├── config.py            # Constants, TARGET_MODELS dict, paths
├── models.py            # Dataclasses: MinerListing, TradeHistory, Alert
├── simplemining_api.py  # REST client for SimpleMining marketplace (4 endpoints)
├── alert_engine.py      # Multi-benchmark discount logic, revenue calc, sent-alert tracking
├── telegram_bot.py      # Message formatting and Telegram delivery
└── main.py              # Entry point orchestrating the 4-step pipeline
```

## Alert Logic (Multi-Benchmark + Quality Filter)
- **Quality gate**: Skip listings with efficiency_jth > 17.5 (no deal_score gate — SimpleMining doesn't provide it)
- **Primary trigger**: >=60% off last trade price
- **Fallback trigger**: >=60% off 90-day midpoint (if no last trade data)
- **No data**: skip listing (no reliable benchmark)
- All 3 benchmarks (last trade, ATH, 90d avg) shown in alert messages for context
- Revenue/hosting/ROI computed locally (hashprice * hashrate, power * $/kWh)

## API Endpoints (all public, no auth)
- `GET /v1/common/hash-price` — hashprice as string, cast to float
- `GET /v1/marketplace/stats` — summary stats (count, price range)
- `GET /v1/marketplace/offers/average-price` — ALL trade history in one call
- `GET /v1/marketplace/listings?size=1000&model=...` — all listings, single call

## Key Differences from Blockware Bot
- REST API (not GraphQL), 4 total API calls per run (vs ~100+)
- Trade stats computed client-side from raw offer arrays
- No deal_score, no 24h hashrate, no bundles
- Revenue/cost computed locally (not from API)

## Deployment
- **Platform**: GitHub Actions cron (every 10 min)
- **Secrets needed**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **State**: `data/sent_alerts.json` committed back by Actions

## Maintenance
- **Quarterly**: Review `TARGET_MODELS` in `src/config.py`. New ASIC models won't trigger alerts until added.
