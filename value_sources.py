"""
External data sources for player trade values and projections
Optimized for REDRAFT leagues (not dynasty)
"""
import requests
import pandas as pd
from typing import Optional
import fantasy_config as config

class FantasyCalcClient:
    """
    Client for FantasyCalc trade values
    These represent PERCEIVED market value based on actual trades
    """
    
    def __init__(self):
        self.api_url = config.FANTASYCALC_API
    
    def get_redraft_values(self) -> pd.DataFrame:
        """
        Get current redraft trade values from FantasyCalc
        Returns perceived market value (what people are actually trading for)
        """
        print("Fetching FantasyCalc trade values (perceived market value)...")
        
        params = {
            'isDynasty': 'false',  # CRITICAL: Redraft only!
            'numQbs': config.NUM_QBS,
            'numTeams': config.NUM_TEAMS,
            'ppr': config.get_ppr_value()
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            values = []
            for item in data:
                player = item.get('player', {})
                values.append({
                    'player_name': player.get('name'),
                    'position': player.get('position'),
                    'nfl_team': player.get('maybeTeam', 'FA'),
                    'perceived_value': item.get('value', 0),
                    'overall_rank': item.get('overallRank', 999),
                    'position_rank': item.get('positionRank', 999),
                    'trend_30day': item.get('trend30Day', 0)
                })
            
            df = pd.DataFrame(values)
            
            # Apply position scarcity multipliers for redraft
            df['perceived_value_adjusted'] = df.apply(
                lambda row: row['perceived_value'] * config.POSITION_SCARCITY_MULTIPLIERS.get(row['position'], 1.0),
                axis=1
            )
            
            print(f"✓ Loaded {len(df)} players from FantasyCalc")
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching FantasyCalc data: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return pd.DataFrame()


class FantasyProsClient:
    """
    Client for FantasyPros rest-of-season rankings
    These represent FORECASTED value based on expert consensus
    """
    
    # FantasyPros doesn't have a public API, but their rankings pages are structured
    # This is a placeholder - in practice you'd either scrape or use their paid API
    
    def get_rest_of_season_rankings(self) -> pd.DataFrame:
        """
        Get rest-of-season rankings from FantasyPros
        Note: This requires either scraping or a paid API key
        """
        print("FantasyPros rankings require manual download or paid API access")
        print("Using ESPN projections as forecasted value instead...")
        return pd.DataFrame()


class AlternativeValueSource:
    """
    Alternative value sources if primary sources fail
    Can use ADP, consensus rankings, etc.
    """
    
    @staticmethod
    def get_adp_values() -> pd.DataFrame:
        """
        Get ADP (Average Draft Position) as a proxy for perceived value
        Lower ADP = higher value
        """
        print("Fetching ADP data as alternative value source...")
        
        # Fantasy Football Calculator API (free ADP data)
        url = "https://fantasyfootballcalculator.com/api/v1/adp/ppr"
        
        params = {
            'teams': config.NUM_TEAMS,
            'year': config.SEASON
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            players = data.get('players', [])
            adp_values = []
            
            for player in players:
                # Convert ADP to a value (inverse relationship)
                # Player with ADP 1 gets highest value
                adp = player.get('adp', 999)
                value = max(1000 - (adp * 5), 0)  # Scale ADP to value points
                
                adp_values.append({
                    'player_name': player.get('name'),
                    'position': player.get('position'),
                    'nfl_team': player.get('team', 'FA'),
                    'adp': adp,
                    'perceived_value': value
                })
            
            df = pd.DataFrame(adp_values)
            print(f"✓ Loaded ADP for {len(df)} players")
            return df
            
        except Exception as e:
            print(f"✗ Error fetching ADP data: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def generate_synthetic_forecasts(perceived_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate synthetic forecasted values based on perceived values
        Only use this as a last resort for testing
        """
        import numpy as np
        
        print("⚠ Generating synthetic forecast data (for testing only)")
        
        df = perceived_df.copy()
        
        # Add realistic variance to create "forecasted" values
        # Players with high perceived value might be overvalued or undervalued
        np.random.seed(42)  # For reproducibility
        
        df['forecasted_value'] = df['perceived_value'] * np.random.uniform(0.7, 1.3, len(df))
        
        # Add some position-based biases (RBs often overvalued early season)
        df.loc[df['position'] == 'RB', 'forecasted_value'] *= np.random.uniform(0.8, 1.0, len(df[df['position'] == 'RB']))
        df.loc[df['position'] == 'WR', 'forecasted_value'] *= np.random.uniform(1.0, 1.2, len(df[df['position'] == 'WR']))
        
        return df


def get_perceived_values() -> pd.DataFrame:
    """
    Main function to get perceived values (market value)
    Tries multiple sources in order of preference
    """
    # Try FantasyCalc first (best source for redraft trade values)
    client = FantasyCalcClient()
    df = client.get_redraft_values()
    
    if not df.empty:
        return df
    
    # Fallback to ADP if FantasyCalc fails
    print("Falling back to ADP as perceived value...")
    df = AlternativeValueSource.get_adp_values()
    
    if not df.empty:
        return df
    
    print("✗ Could not fetch perceived values from any source")
    return pd.DataFrame()


def get_forecasted_values(espn_projections: pd.DataFrame = None) -> pd.DataFrame:
    """
    Main function to get forecasted values (expected future performance)
    For redraft, this should be REST OF SEASON projections
    """
    # If ESPN projections provided, use those
    if espn_projections is not None and not espn_projections.empty:
        print("✓ Using ESPN rest-of-season projections as forecasted value")
        return espn_projections
    
    # Try FantasyPros if available
    fp_client = FantasyProsClient()
    df = fp_client.get_rest_of_season_rankings()
    
    if not df.empty:
        return df
    
    print("⚠ No forecasted values available - will need ESPN projections")
    return pd.DataFrame()


def combine_recent_performance_with_projections(
    projections: pd.DataFrame,
    recent_stats: pd.DataFrame,
    weight_recent: float = 0.4
) -> pd.DataFrame:
    """
    Combine rest-of-season projections with recent performance
    In redraft, recent performance is more predictive than preseason
    
    Args:
        projections: Rest of season projections
        recent_stats: Recent game performance (last 3-4 weeks)
        weight_recent: How much to weight recent performance (0-1)
    """
    if recent_stats.empty:
        return projections
    
    merged = projections.merge(recent_stats, on='player_name', how='left')
    
    # Adjust projections based on recent performance
    # If player is hot, bump up projection; if cold, lower it
    merged['recent_avg'] = merged['recent_avg'].fillna(0)
    
    # Calculate adjusted forecast
    merged['forecasted_value_adjusted'] = (
        merged['rest_of_season_projection'] * (1 - weight_recent) +
        merged['recent_avg'] * 13 * weight_recent  # 13 weeks remaining on average
    )
    
    return merged