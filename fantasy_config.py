"""
Configuration settings for ESPN Fantasy Football Trade Analyzer
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ESPN League Settings
LEAGUE_ID = int(os.getenv('LEAGUE_ID', '0'))
SEASON = int(os.getenv('SEASON', '2025'))
ESPN_S2 = os.getenv('ESPN_S2', '')
SWID = os.getenv('SWID', '')

# Your Team Settings
YOUR_TEAM_NAME = os.getenv('YOUR_TEAM_NAME', '')

# League Format Settings (REDRAFT SPECIFIC)
SCORING_FORMAT = os.getenv('SCORING_FORMAT', 'ppr').lower()
NUM_TEAMS = int(os.getenv('NUM_TEAMS', '12'))
NUM_QBS = int(os.getenv('NUM_QBS', '1'))

# PPR scoring mapping for FantasyCalc API
PPR_MAPPING = {
    'ppr': 1,
    'half_ppr': 0.5,
    'standard': 0
}

# Position scarcity multipliers for redraft leagues
# Adjust these based on league scoring and roster requirements
POSITION_SCARCITY_MULTIPLIERS = {
    'QB': 0.8,  # QB is less scarce in 1QB leagues
    'RB': 1.2,  # RBs are typically scarce
    'WR': 1.0,  # WRs baseline
    'TE': 1.1,  # TEs somewhat scarce
    'K': 0.5,   # Kickers are replaceable
    'D/ST': 0.6 # Defense/ST replaceable
}

# Analysis parameters for redraft
MIN_PERCEIVED_VALUE = 5  # Ignore players below this value (waiver wire)
RECENT_GAMES_WEIGHT = 0.4  # How much to weight recent performance (0-1)

# Thresholds for trade analysis
MIN_DISCOUNT_THRESHOLD = 10  # Minimum discount % to consider undervalued
MIN_PREMIUM_THRESHOLD = -10  # Minimum premium % to consider overvalued
MIN_TRADE_VALUE = 100  # Minimum perceived value to consider for trades

# Players you never want to trade (add player names here)
UNTOUCHABLE_PLAYERS = []  # e.g., ['Christian McCaffrey', 'Josh Allen']

# External API URLs
FANTASYCALC_API = "https://api.fantasycalc.com/values/current"

# Output settings
OUTPUT_DIR = "output"
EXPORT_CSV = True
EXPORT_JSON = True

def validate_config():
    """Validate that required configuration is set"""
    if not LEAGUE_ID or LEAGUE_ID == 0:
        raise ValueError("LEAGUE_ID must be set in .env file")
    
    if not SEASON:
        raise ValueError("SEASON must be set in .env file")
    
    if not ESPN_S2 or not SWID:
        print("WARNING: ESPN_S2 and SWID not set. You'll need these for private leagues.")
    
    if SCORING_FORMAT not in PPR_MAPPING:
        raise ValueError(f"SCORING_FORMAT must be one of: {list(PPR_MAPPING.keys())}")
    
    return True

def get_ppr_value():
    """Get PPR value for API calls"""
    return PPR_MAPPING.get(SCORING_FORMAT, 1)
