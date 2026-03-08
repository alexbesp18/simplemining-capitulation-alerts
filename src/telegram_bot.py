"""
Telegram notification sender.
Uses the Telegram Bot API directly via requests (no library dependency).
"""

import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _fmt_discount_line(label: str, pct: float | None, benchmark: float | None, primary: bool = False) -> str:
    """Format a single discount benchmark line."""
    prefix = "\u27a4 " if primary else "   "
    if pct is not None and benchmark is not None:
        return f"{prefix}{pct:.0f}% off {label} (${benchmark:,.0f})"
    return f"{prefix}{label}: no data"


def format_alert(alert) -> str:
    """Format an Alert into a Telegram message with HTML formatting."""
    l = alert.listing

    # ROI string
    if alert.months_to_roi is not None:
        roi_str = f"{alert.months_to_roi:.1f} months"
    else:
        roi_str = "N/A (negative profit)"

    # Build discount lines
    disc_lines = []
    disc_lines.append(_fmt_discount_line(
        "Last Trade", alert.discount_vs_last_trade, alert.last_trade_price, primary=True))
    disc_lines.append(_fmt_discount_line(
        "ATH", alert.discount_vs_ath, alert.ath_price))
    disc_lines.append(_fmt_discount_line(
        "90d Avg", alert.discount_vs_90d_mid, alert.range_90d_midpoint))
    discounts_block = "\n".join(disc_lines)

    msg = (
        f"\U0001f6a8\U0001f6a8\U0001f6a8 <b>CAPITULATION ALERT</b> \U0001f6a8\U0001f6a8\U0001f6a8\n"
        f"<i>via SimpleMining.io</i>\n"
        f"\n"
        f"<b>{l.model_name}</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b0 <b>${l.listed_price:,.0f}</b>\n"
        f"\n"
        f"<b>Discounts:</b>\n"
        f"{discounts_block}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4ca ${l.price_per_hashrate:.2f}/TH\n"
        f"\u26cf Hashrate: {l.hashrate_th:.0f} TH/s\n"
        f"\u26a1 Efficiency: {l.efficiency_jth:.1f} J/TH  |  Power: {l.power_kw:.2f} kW\n"
        f"\U0001f464 Seller: {l.seller_name}\n"
        f"\U0001f4cd Location: {l.miner_location}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b5 Est. Monthly Revenue: ${alert.est_monthly_revenue:,.2f}\n"
        f"\U0001f4b5 Est. Monthly Hosting: ${alert.est_monthly_hosting_cost:,.2f}\n"
        f"\U0001f4b5 Est. Monthly Profit: ${alert.est_monthly_profit:,.2f}\n"
        f"\u23f1 Breakeven: {roi_str}\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"Hashprice: ${alert.hashprice_usd}/PH/day\n"
        f"\n"
        f'\U0001f517 <a href="{l.link}">VIEW ON SIMPLEMINING</a>'
    )
    return msg


def _primary_discount(alert) -> str:
    """Short string describing the primary discount for dry-run / log output."""
    if alert.discount_vs_last_trade is not None:
        return f"{alert.discount_vs_last_trade:.0f}% off last trade"
    if alert.discount_vs_90d_mid is not None:
        return f"{alert.discount_vs_90d_mid:.0f}% off 90d avg"
    return "discount unknown"


def send_alert(alert) -> bool:
    """Send a single alert to Telegram. Returns True on success."""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[DRY RUN] Would send alert for listing #{alert.listing.listing_id}: "
              f"{alert.listing.model_name} @ ${alert.listing.listed_price:,.0f} "
              f"({_primary_discount(alert)})")
        return True

    msg = format_alert(alert)
    resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=10)

    if resp.status_code == 200:
        return True
    else:
        print(f"Telegram error {resp.status_code}: {resp.text}")
        return False


def send_summary(total_listings: int, alerts_sent: int):
    """Log a run summary (console only, no Telegram spam)."""
    print(f"[Summary] Scanned {total_listings} listings | "
          f"Alerts sent this run: {alerts_sent}")


def format_daily_digest(deals, hashprice: float, total_listings: int) -> str:
    """Format a daily digest message with top deals by $/TH."""
    from datetime import datetime, timezone, timedelta
    ct = datetime.now(timezone(timedelta(hours=-5)))
    date_str = ct.strftime("%b %-d, %Y")

    count = len(deals)
    footer_label = f"Top {count}" if count < 5 else "Top 5"
    if count == total_listings:
        footer_label = f"All {count}"

    lines = [
        f"\U0001f4cb <b>Daily Digest</b> \u2014 {date_str}",
        f"<i>via SimpleMining.io</i>",
        f"",
        f"\u26a1 ${hashprice:.2f}/PH/day | {total_listings} listings",
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501",
    ]

    for i, deal in enumerate(deals, 1):
        l = deal.listing
        # Short model name: strip "Antminer " prefix
        short_name = l.model_name.replace("Antminer ", "")

        # Discount line
        if deal.discount_vs_last_trade is not None:
            pct = deal.discount_vs_last_trade
            bench = deal.last_trade_price
            label = "last"
        elif deal.discount_vs_90d_mid is not None:
            pct = deal.discount_vs_90d_mid
            bench = deal.range_90d_midpoint
            label = "90d"
        else:
            pct = None
            bench = None
            label = ""

        if pct is not None and bench is not None:
            if pct > 0:
                disc_str = f"-{pct:.0f}% {label} ${bench:,.0f}"
            else:
                disc_str = f"+{abs(pct):.0f}% above {label} ${bench:,.0f}"
        else:
            disc_str = "no trade data"

        # ROI
        roi_str = f"ROI {deal.months_to_roi:.1f}mo" if deal.months_to_roi else "ROI N/A"

        lines.append(f"")
        lines.append(f"<b>{i}.</b> <b>{short_name}</b> \u2014 <b>${l.listed_price:,.0f}</b> (${l.price_per_hashrate:.2f}/TH)")
        lines.append(f"   {disc_str} | Profit ${deal.est_monthly_profit:,.0f}/mo | {roi_str}")
        lines.append(f"   \U0001f4cd {l.miner_location or 'Unknown'} | <a href=\"{l.link}\">View deal</a>")

    lines.append(f"")
    lines.append(f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501")
    lines.append(f"<i>{footer_label} by $/TH (new-gen, \u226417.5 J/TH).\n60%+ off capitulation alerts sent separately.</i>")

    return "\n".join(lines)


def send_daily_digest(deals, hashprice: float, total_listings: int) -> bool:
    """Send the daily digest to Telegram. Returns True on success."""
    if not deals:
        print("[Digest] No qualified listings. Skipping digest.")
        return False

    msg = format_daily_digest(deals, hashprice, total_listings)

    if not BOT_TOKEN or not CHAT_ID:
        print(f"[DRY RUN] Daily digest ({len(deals)} deals):")
        print(msg)
        return True

    resp = requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=10)

    if resp.status_code == 200:
        print(f"[Digest] Sent daily digest with {len(deals)} deals.")
        return True
    else:
        print(f"[Digest] Telegram error {resp.status_code}: {resp.text}")
        return False
