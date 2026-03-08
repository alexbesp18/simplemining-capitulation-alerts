# SimpleMining Capitulation Alert Bot

## Overview
Python bot that monitors SimpleMining.io miner marketplace for extreme bargain deals on new-gen Bitcoin miners (S21 class). Sends Telegram alerts when high-quality listings (<=17.5 J/TH) appear at >=60% discount from last trade price (or 90-day average as fallback). Revenue/cost/ROI computed locally from hashprice.

## Commands
```bash
# Capitulation alerts (dry-run)
python -m src.main

# Daily digest (dry-run)
python -m src.digest

# With Telegram
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python -m src.main
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python -m src.digest
```

## Architecture
```
src/
├── config.py            # Constants, TARGET_MODELS dict, paths
├── models.py            # Dataclasses: MinerListing, TradeHistory, Alert
├── simplemining_api.py  # REST client for SimpleMining marketplace (4 endpoints)
├── alert_engine.py      # Multi-benchmark discount logic, revenue calc, sent-alert tracking
├── telegram_bot.py      # Message formatting and Telegram delivery
├── main.py              # Entry point: capitulation alerts (every 10 min)
└── digest.py            # Entry point: daily digest (top 5 by $/TH, daily)
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

## Daily Digest
- **Schedule**: Daily at 9:00 AM CT (`0 14 * * *`)
- **Format**: Top 5 listings by $/TH with discount, profit, ROI per listing
- **Quality gate**: Same efficiency filter (<=17.5 J/TH), no discount threshold
- **Stateless**: No dedup tracking — shows current market snapshot daily
- **Edge cases**: 0 qualified listings → silent skip; <5 listings → sends what exists

## Deployment
- **Capitulation alerts**: GitHub Actions cron every 10 min (`check_deals.yml`)
- **Daily digest**: GitHub Actions cron daily at 9 AM CT (`daily_digest.yml`)
- **Secrets needed**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **State**: `data/sent_alerts.json` committed back by Actions (alerts only, not digest)

## Maintenance
- **Quarterly**: Review `TARGET_MODELS` in `src/config.py`. New ASIC models won't trigger alerts until added.
