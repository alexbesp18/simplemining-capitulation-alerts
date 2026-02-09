"""
SimpleMining.io REST API client.
All endpoints are public (no auth). Full trade history in one call.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import BASE_URL, TARGET_MODELS, RANGE_WINDOW_DAYS
from .models import MinerListing, TradeHistory

# Retry on transient HTTP errors (5xx, timeouts, connection errors)
_RETRY_DECORATOR = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError,
                                   requests.exceptions.Timeout,
                                   requests.exceptions.HTTPError)),
    reraise=True,
)


@_RETRY_DECORATOR
def _get(path: str, params: Optional[dict] = None) -> dict:
    """GET request helper with retry. Validates success field, returns data."""
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if not body.get("success"):
        raise RuntimeError(f"API error on {path}: {body}")
    return body["data"]


def fetch_hashprice() -> float:
    """GET /v1/common/hash-price — returns $/PH/day as float."""
    data = _get("/common/hash-price")
    return float(data)


def fetch_marketplace_stats() -> dict:
    """GET /v1/marketplace/stats — summary stats for logging."""
    return _get("/marketplace/stats")


def _build_model_name_to_id() -> Dict[str, int]:
    """Reverse lookup: model name -> model id from TARGET_MODELS."""
    return {v["name"]: k for k, v in TARGET_MODELS.items()}


def fetch_trade_histories() -> Dict[int, TradeHistory]:
    """
    GET /v1/marketplace/offers/average-price
    Returns all trade history in ONE call. We filter to TARGET_MODELS
    and compute ATH, ATL, last trade, 90d stats client-side.
    """
    data = _get("/marketplace/offers/average-price")
    name_to_id = _build_model_name_to_id()
    cutoff = datetime.now(timezone.utc) - timedelta(days=RANGE_WINDOW_DAYS)

    results: Dict[int, TradeHistory] = {}

    for entry in data:
        model_name = entry.get("model_name", "")
        model_id = name_to_id.get(model_name)
        if model_id is None:
            continue

        offers = entry.get("offers", [])
        num_units_sold = entry.get("num_units_sold", len(offers))
        avg_price = entry.get("avg_price")

        if not offers:
            results[model_id] = TradeHistory(
                model_name=model_name,
                avg_price=avg_price,
                num_units_sold=num_units_sold,
                ath_price=None,
                atl_price=None,
                last_trade_price=None,
                last_trade_date=None,
                range_90d_high=None,
                range_90d_low=None,
                range_90d_midpoint=None,
                range_90d_count=0,
            )
            continue

        # Sort by accepted_at ascending
        sorted_offers = sorted(offers, key=lambda o: o.get("accepted_at", ""))

        # Extract prices
        prices = [o["amount"] for o in sorted_offers if o.get("amount")]
        ath_price = max(prices) if prices else None
        atl_price = min(prices) if prices else None

        # Last trade
        last = sorted_offers[-1]
        last_trade_price = last.get("amount")
        last_trade_date = last.get("accepted_at")

        # 90-day window
        recent_prices = []
        for o in sorted_offers:
            accepted = o.get("accepted_at", "")
            if not accepted:
                continue
            try:
                ts = datetime.fromisoformat(accepted.replace("Z", "+00:00"))
                if ts >= cutoff and o.get("amount"):
                    recent_prices.append(o["amount"])
            except (ValueError, TypeError):
                continue

        range_90d_high = max(recent_prices) if recent_prices else None
        range_90d_low = min(recent_prices) if recent_prices else None
        range_90d_midpoint = (
            round((range_90d_high + range_90d_low) / 2, 2)
            if range_90d_high is not None and range_90d_low is not None
            else None
        )

        results[model_id] = TradeHistory(
            model_name=model_name,
            avg_price=avg_price,
            num_units_sold=num_units_sold,
            ath_price=ath_price,
            atl_price=atl_price,
            last_trade_price=last_trade_price,
            last_trade_date=last_trade_date,
            range_90d_high=range_90d_high,
            range_90d_low=range_90d_low,
            range_90d_midpoint=range_90d_midpoint,
            range_90d_count=len(recent_prices),
        )

    return results


@_RETRY_DECORATOR
def fetch_current_listings() -> List[MinerListing]:
    """
    GET /v1/marketplace/listings?size=1000&model=85&model=86...
    Single call gets all listings. Filter to TARGET_MODELS only.
    """
    params = [("size", 1000)]
    for model_id in TARGET_MODELS:
        params.append(("model", model_id))

    resp = requests.get(f"{BASE_URL}/marketplace/listings", params=params, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if not body.get("success"):
        raise RuntimeError(f"API error on /marketplace/listings: {body}")

    # Nested: data.data[...]
    raw_listings = body["data"].get("data", [])
    listings: List[MinerListing] = []

    for item in raw_listings:
        model = item.get("model", {})
        model_id = model.get("id")
        if model_id not in TARGET_MODELS:
            continue

        specs = TARGET_MODELS[model_id]
        seller = item.get("seller", {})

        # Count pending offers (not accepted)
        offers = item.get("offers") or []
        pending_count = sum(1 for o in offers if not o.get("is_accepted"))

        listing_id = item["id"]
        link = f"https://app.simplemining.io/marketplace/{listing_id}"

        listings.append(MinerListing(
            listing_id=listing_id,
            miner_id=item.get("idMiner", 0),
            miner_name=item.get("minerName", ""),
            miner_location=item.get("minerLocation", ""),
            serial=item.get("serial", ""),
            listed_price=item.get("listedPrice", 0),
            price_per_hashrate=item.get("pricePerHashrate", 0),
            model_id=model_id,
            model_name=specs["name"],
            hashrate_th=specs["hashrate"],
            power_kw=specs["power"],
            efficiency_jth=specs["jth"],
            seller_name=seller.get("name", "Unknown"),
            created_at=item.get("createdAt", ""),
            pending_offer_count=pending_count,
            link=link,
        ))

    return listings
