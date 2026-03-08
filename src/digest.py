"""
Daily digest entry point. Called by GitHub Actions once per day.
Sends a Telegram message with the top 5 cheapest listings by $/TH.
"""

import os
import sys
from dotenv import load_dotenv
from .simplemining_api import fetch_hashprice, fetch_marketplace_stats, fetch_trade_histories, fetch_current_listings
from .alert_engine import find_top_deals
from .telegram_bot import send_daily_digest
from .config import DEFAULT_HOSTING_COST_KWH

load_dotenv()


def main():
    print("=" * 60)
    print("SimpleMining Daily Digest - Starting run")
    print("=" * 60)

    try:
        hosting_cost = float(os.environ.get("HOSTING_COST_PER_KWH", DEFAULT_HOSTING_COST_KWH))

        # 1. Get hashprice
        print("[1/3] Fetching hashprice...")
        hashprice = fetch_hashprice()
        print(f"  Hashprice: ${hashprice}/PH/day")

        # 2. Get trade histories
        print("[2/3] Fetching trade histories...")
        trade_histories = fetch_trade_histories()
        print(f"  Got trade history for {len(trade_histories)} models")

        # 3. Get current listings
        print("[3/3] Fetching current listings...")
        listings = fetch_current_listings()
        total_count = len(listings)
        print(f"  Found {total_count} target-model listings")

        # Find top deals by $/TH
        deals = find_top_deals(listings, trade_histories, hashprice, hosting_cost)
        print(f"  Top deals found: {len(deals)}")

        # Send digest
        send_daily_digest(deals, hashprice, total_count)

    except Exception as e:
        print(f"Digest failed (non-fatal): {e}")
        # Exit 0 — digest is non-critical, don't fail the workflow

    print("Done.")


if __name__ == "__main__":
    main()
