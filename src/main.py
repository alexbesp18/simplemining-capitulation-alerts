"""
Main entry point. Called by GitHub Actions every 10 minutes.
"""

import os
import sys
from dotenv import load_dotenv
from .simplemining_api import fetch_hashprice, fetch_marketplace_stats, fetch_trade_histories, fetch_current_listings
from .alert_engine import find_capitulation_deals, mark_alerts_sent
from .telegram_bot import send_alert, send_summary
from .config import DEFAULT_HOSTING_COST_KWH

load_dotenv()


def main():
    print("=" * 60)
    print("SimpleMining Capitulation Alert Bot - Starting run")
    print("=" * 60)

    hosting_cost = float(os.environ.get("HOSTING_COST_PER_KWH", DEFAULT_HOSTING_COST_KWH))

    # 1. Get hashprice
    print("[1/4] Fetching hashprice...")
    try:
        hashprice = fetch_hashprice()
    except Exception as e:
        print(f"ERROR fetching hashprice: {e}")
        sys.exit(1)

    print(f"  Hashprice: ${hashprice}/PH/day")

    # 2. Get marketplace stats (logging only)
    try:
        stats = fetch_marketplace_stats()
        print(f"  Marketplace: {stats.get('count', '?')} total listings | "
              f"${stats.get('minPrice', '?')}-${stats.get('maxPrice', '?')} range")
    except Exception as e:
        print(f"  Warning: could not fetch marketplace stats: {e}")

    # 3. Get trade histories for all target models
    print("[2/4] Fetching trade histories...")
    try:
        trade_histories = fetch_trade_histories()
    except Exception as e:
        print(f"ERROR fetching trade histories: {e}")
        sys.exit(1)

    print(f"  Got trade history for {len(trade_histories)} models")
    for model_id, hist in trade_histories.items():
        last = f"${hist.last_trade_price:,.0f}" if hist.last_trade_price else "none"
        mid = f"${hist.range_90d_midpoint:,.0f}" if hist.range_90d_midpoint else "none"
        print(f"    {hist.model_name}: {hist.num_units_sold} sold | last={last} | 90d_mid={mid}")

    # 4. Get current listings
    print("[3/4] Fetching current listings...")
    try:
        listings = fetch_current_listings()
    except Exception as e:
        print(f"ERROR fetching listings: {e}")
        sys.exit(1)

    print(f"  Found {len(listings)} target-model listings")

    # 5. Find capitulation deals
    print("[4/4] Scanning for 60%+ off deals (efficiency <=17.5 J/TH)...")
    alerts = find_capitulation_deals(listings, trade_histories, hashprice, hosting_cost)

    if not alerts:
        print("  No capitulation deals found this run.")
    else:
        print(f"  FOUND {len(alerts)} CAPITULATION DEAL(S)!")
        sent_alerts = []
        for alert in alerts:
            l = alert.listing
            if alert.discount_vs_last_trade is not None:
                disc_str = f"{alert.discount_vs_last_trade:.0f}% off last trade ${alert.last_trade_price:,.0f}"
            elif alert.discount_vs_90d_mid is not None:
                disc_str = f"{alert.discount_vs_90d_mid:.0f}% off 90d avg ${alert.range_90d_midpoint:,.0f}"
            else:
                disc_str = "discount unknown"
            print(f"  -> {l.model_name} @ ${l.listed_price:,.0f} "
                  f"({disc_str}) "
                  f"${l.price_per_hashrate:.2f}/TH | {l.efficiency_jth} J/TH")
            if send_alert(alert):
                sent_alerts.append(alert)

        if sent_alerts:
            mark_alerts_sent(sent_alerts)
        print(f"  Sent {len(sent_alerts)}/{len(alerts)} alerts to Telegram")

    send_summary(len(listings), len(alerts))
    print("Done.")


if __name__ == "__main__":
    main()
