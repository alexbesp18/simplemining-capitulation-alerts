# SimpleMining Capitulation Alert Bot

Monitors the SimpleMining.io miner marketplace for extreme bargain deals
on new-gen Bitcoin miners (S21, S21+, S21 Pro, S21 XP, S21+ Hydro) and sends
Telegram alerts when high-quality listings appear at >=60% discount from their
last trade price.

## How it works

- Polls SimpleMining's public REST API (no auth needed)
- Fetches trade history to compute benchmarks (last trade, 90-day midpoint)
- **Quality filters**: Skips offers with efficiency > 17.5 J/TH
- **Primary trigger**: >=60% off last trade price
- **Fallback**: >=60% off 90-day midpoint (if no last trade data)
- **No data**: skips offer entirely (no reliable benchmark)
- Each alert includes revenue/ROI estimates based on configurable hosting cost
- Tracks sent alert IDs in `data/sent_alerts.json` to avoid duplicates (capped at 2000)
- State is committed back to repo by GitHub Actions

## Target models

| Model | Hashrate | Efficiency |
|-------|----------|------------|
| Antminer S21 (188T/195T/200T) | 188–200 TH/s | 17.5 J/TH |
| Antminer S21+ (216T/235T) | 216–235 TH/s | 15.0–15.5 J/TH |
| Antminer S21 Pro (234T) | 234 TH/s | 15.0 J/TH |
| Antminer S21 XP (270T) | 270 TH/s | 13.5 J/TH |
| Antminer S21+ Hydro (395T) | 395 TH/s | 14.0 J/TH |

## Setup

1. Create a Telegram bot via @BotFather, get the token
2. Get your chat ID (message @userinfobot or create a channel)
3. Add secrets to GitHub repo: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
4. Push to GitHub — the cron runs every 10 minutes automatically

## Local testing

```bash
cp .env.example .env
# Edit .env with your real tokens
pip install -r requirements.txt
python -m src.main
```

Without Telegram credentials set, it runs in dry-run mode (prints alerts to console).
