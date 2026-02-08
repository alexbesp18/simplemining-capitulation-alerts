from dataclasses import dataclass
from typing import Optional


@dataclass
class MinerListing:
    listing_id: int
    miner_id: int
    miner_name: str
    miner_location: str
    serial: str
    listed_price: float
    price_per_hashrate: float
    model_id: int
    model_name: str
    hashrate_th: float
    power_kw: float
    efficiency_jth: float
    seller_name: str
    created_at: str
    pending_offer_count: int
    link: str


@dataclass
class TradeHistory:
    model_name: str
    avg_price: Optional[float]
    num_units_sold: int
    ath_price: Optional[float]
    atl_price: Optional[float]
    last_trade_price: Optional[float]
    last_trade_date: Optional[str]
    range_90d_high: Optional[float]
    range_90d_low: Optional[float]
    range_90d_midpoint: Optional[float]
    range_90d_count: int


@dataclass
class Alert:
    listing: MinerListing
    hashprice_usd: float
    est_monthly_revenue: float
    est_monthly_hosting_cost: float
    est_monthly_profit: float
    months_to_roi: Optional[float]
    # Primary benchmark (trigger)
    last_trade_price: Optional[float]
    discount_vs_last_trade: Optional[float]
    # Context benchmarks
    ath_price: Optional[float]
    discount_vs_ath: Optional[float]
    range_90d_midpoint: Optional[float]
    discount_vs_90d_mid: Optional[float]
