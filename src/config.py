BASE_URL = "https://api.simplemining.io/v1"

DISCOUNT_THRESHOLD = 60  # percent off last trade (or 90d midpoint fallback)

MAX_EFFICIENCY_JTH = 17.5  # skip listings above this J/TH

RANGE_WINDOW_DAYS = 90  # days for windowed high/low stats

DEFAULT_HOSTING_COST_KWH = 0.08  # $/kWh default if not set in env

SENT_ALERTS_PATH = "data/sent_alerts.json"
MAX_SENT_IDS = 2000

# ── TARGET MINER MODELS ──────────────────────────────────────────
# SimpleMining model_id -> specs
# hashrate in TH/s, power in kW, jth in J/TH
TARGET_MODELS = {
    # S21 base
    87:  {"name": "Antminer S21 (188T)", "hashrate": 188, "power": 3.29, "jth": 17.5},
    86:  {"name": "Antminer S21 (195T)", "hashrate": 195, "power": 3.41, "jth": 17.5},
    85:  {"name": "Antminer S21 (200T)", "hashrate": 200, "power": 3.50, "jth": 17.5},
    # S21+
    120: {"name": "Antminer S21+ (216T)", "hashrate": 216, "power": 3.36, "jth": 15.5},
    121: {"name": "Antminer S21+ (235T)", "hashrate": 235, "power": 3.53, "jth": 15.0},
    # S21 Pro
    99:  {"name": "Antminer S21 Pro (234T)", "hashrate": 234, "power": 3.51, "jth": 15.0},
    # S21 XP
    110: {"name": "Antminer S21 XP (270T)", "hashrate": 270, "power": 3.65, "jth": 13.5},
    # S21+ Hydro
    123: {"name": "Antminer S21+ Hydro (395T)", "hashrate": 395, "power": 5.53, "jth": 14.0},
}
