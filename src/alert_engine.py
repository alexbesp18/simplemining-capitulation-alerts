"""
Core alert logic — multi-benchmark with quality filter:
1. Quality gate: skip listings with efficiency_jth > 17.5
2. Primary trigger: >= 60% off last_trade_price
3. Fallback trigger: >= 60% off range_90d_midpoint (if no last trade)
4. No data: skip (no reliable benchmark)
5. All 3 discount percentages computed for context in the alert message.
"""

import json
import os
from typing import List, Dict, Optional
from .models import MinerListing, TradeHistory, Alert
from .config import DISCOUNT_THRESHOLD, SENT_ALERTS_PATH, MAX_SENT_IDS, MAX_EFFICIENCY_JTH, DEFAULT_HOSTING_COST_KWH


def load_sent_alerts() -> set:
    """Load previously alerted listing IDs from JSON file."""
    if os.path.exists(SENT_ALERTS_PATH):
        with open(SENT_ALERTS_PATH, "r") as f:
            data = json.load(f)
            return set(data.get("sent_ids", []))
    return set()


def save_sent_alerts(sent_ids: set):
    """Persist alerted listing IDs to JSON file."""
    os.makedirs(os.path.dirname(SENT_ALERTS_PATH), exist_ok=True)
    trimmed = sorted(sent_ids)[-MAX_SENT_IDS:]
    with open(SENT_ALERTS_PATH, "w") as f:
        json.dump({"sent_ids": trimmed}, f)


def _discount_pct(price: float, benchmark: Optional[float]) -> Optional[float]:
    """Compute discount percentage. Returns None if benchmark is missing or invalid."""
    if benchmark is None or benchmark <= 0:
        return None
    return round((1 - price / benchmark) * 100, 1)


def compute_revenue(
    hashrate_th: float,
    power_kw: float,
    hashprice: float,
    hosting_cost_kwh: float,
) -> tuple[float, float, float]:
    """
    Compute monthly revenue, hosting cost, and profit.
    hashprice is $/PH/day, so revenue = (hashrate_th / 1000) * hashprice * 30.
    """
    monthly_revenue = (hashrate_th / 1000) * hashprice * 30
    monthly_hosting = power_kw * 24 * 30 * hosting_cost_kwh
    monthly_profit = monthly_revenue - monthly_hosting
    return round(monthly_revenue, 2), round(monthly_hosting, 2), round(monthly_profit, 2)


def find_capitulation_deals(
    listings: List[MinerListing],
    trade_histories: Dict[int, TradeHistory],
    hashprice: float,
    hosting_cost_kwh: float,
) -> List[Alert]:
    """
    Scan all listings and return those meeting quality gate + discount threshold.
    Quality gate: efficiency_jth <= 17.5 (no deal_score gate — SimpleMining doesn't have it).
    Primary trigger: >= DISCOUNT_THRESHOLD% off last trade.
    Fallback trigger: >= DISCOUNT_THRESHOLD% off 90d midpoint.
    No benchmark data: skip.
    """
    sent_ids = load_sent_alerts()
    alerts = []

    for listing in listings:
        if listing.listing_id in sent_ids:
            continue

        # Quality gate: efficiency
        if listing.efficiency_jth > MAX_EFFICIENCY_JTH:
            continue

        price = listing.listed_price

        # Resolve trade history for this model
        history = trade_histories.get(listing.model_id)

        last_trade = history.last_trade_price if history else None
        midpoint_90d = history.range_90d_midpoint if history else None
        ath = history.ath_price if history else None

        # Compute all discounts for context
        disc_last = _discount_pct(price, last_trade)
        disc_ath = _discount_pct(price, ath)
        disc_mid = _discount_pct(price, midpoint_90d)

        # Trigger decision: last trade first, then 90d midpoint fallback
        triggered = False
        if disc_last is not None and disc_last >= DISCOUNT_THRESHOLD:
            triggered = True
        elif disc_last is None and disc_mid is not None and disc_mid >= DISCOUNT_THRESHOLD:
            triggered = True

        if not triggered:
            continue

        # Compute revenue/cost/ROI
        revenue, hosting, profit = compute_revenue(
            listing.hashrate_th, listing.power_kw, hashprice, hosting_cost_kwh
        )
        months_roi = round(price / profit, 1) if profit > 0 else None

        alerts.append(Alert(
            listing=listing,
            hashprice_usd=hashprice,
            est_monthly_revenue=revenue,
            est_monthly_hosting_cost=hosting,
            est_monthly_profit=profit,
            months_to_roi=months_roi,
            last_trade_price=last_trade,
            discount_vs_last_trade=disc_last,
            ath_price=ath,
            discount_vs_ath=disc_ath,
            range_90d_midpoint=midpoint_90d,
            discount_vs_90d_mid=disc_mid,
        ))

    return alerts


def find_top_deals(
    listings: List[MinerListing],
    trade_histories: Dict[int, TradeHistory],
    hashprice: float,
    hosting_cost_kwh: float,
    top_n: int = 5,
) -> List[Alert]:
    """
    Return the top N cheapest listings by $/TH for the daily digest.
    Applies efficiency quality gate but NO discount threshold and NO sent_alerts dedup.
    """
    qualified = []

    for listing in listings:
        if listing.efficiency_jth > MAX_EFFICIENCY_JTH:
            continue

        price = listing.listed_price
        history = trade_histories.get(listing.model_id)

        last_trade = history.last_trade_price if history else None
        midpoint_90d = history.range_90d_midpoint if history else None
        ath = history.ath_price if history else None

        disc_last = _discount_pct(price, last_trade)
        disc_ath = _discount_pct(price, ath)
        disc_mid = _discount_pct(price, midpoint_90d)

        revenue, hosting, profit = compute_revenue(
            listing.hashrate_th, listing.power_kw, hashprice, hosting_cost_kwh
        )
        months_roi = round(price / profit, 1) if profit > 0 else None

        qualified.append(Alert(
            listing=listing,
            hashprice_usd=hashprice,
            est_monthly_revenue=revenue,
            est_monthly_hosting_cost=hosting,
            est_monthly_profit=profit,
            months_to_roi=months_roi,
            last_trade_price=last_trade,
            discount_vs_last_trade=disc_last,
            ath_price=ath,
            discount_vs_ath=disc_ath,
            range_90d_midpoint=midpoint_90d,
            discount_vs_90d_mid=disc_mid,
        ))

    # Sort by $/TH ascending (price_per_hashrate)
    qualified.sort(key=lambda a: a.listing.price_per_hashrate)
    return qualified[:top_n]


def mark_alerts_sent(alerts: List[Alert]):
    """Add alerted listing IDs to the sent set and save."""
    sent_ids = load_sent_alerts()
    for alert in alerts:
        sent_ids.add(alert.listing.listing_id)
    save_sent_alerts(sent_ids)
