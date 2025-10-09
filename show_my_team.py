#!/usr/bin/env python3
"""
Quick script to show YOUR team's player value ratios
"""
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values
from trade_analyzer import TradeAnalyzer, TradeReporter
import pandas as pd

print("="*60)
print("YOUR TEAM VALUE ANALYSIS")
print("="*60)

try:
    # Get your team data
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    teams_df = espn.get_all_teams()
    rosters_df = espn.get_all_rosters()
    
    # Merge team info
    rosters_df = rosters_df.merge(teams_df[['team_id', 'wins', 'losses']], on='team_id', how='left')
    
    your_team = "Quinshon Judkins"
    
    # Get perceived values
    print("Getting market values...")
    perceived_df = get_perceived_values()
    
    if perceived_df.empty:
        print("❌ Could not get market values")
        exit(1)
    
    # Get ESPN projections 
    print("Getting ESPN projections...")
    espn_projections = espn.get_rest_of_season_projections()
    
    if espn_projections.empty:
        print("⚠ No ESPN projections available")
        # Create dummy forecasted values for testing
        forecasted_df = pd.DataFrame({
            'player_name': ['Christian McCaffrey', 'Josh Allen', 'A.J. Brown'],
            'forecasted_value': [200, 180, 160]
        })
    else:
        forecasted_df = espn_projections
    
    # Analyze
    analyzer = TradeAnalyzer(rosters_df, perceived_df, forecasted_df)
    analyzer.merge_data_sources()
    analyzer.normalize_values()
    analyzer.calculate_discount_premium()
    
    # Show YOUR team's complete analysis
    your_team_data = analyzer.get_team_data(your_team)
    
    reporter = TradeReporter()
    reporter.print_full_team_ratios(your_team, your_team_data)
    
    # Also show just your rostered players (even without complete data)
    print(f"\n📋 YOUR COMPLETE ROSTER (Team ID 8):")
    print("-"*60)
    your_roster = rosters_df[rosters_df['team_name'] == your_team]
    for _, player in your_roster.iterrows():
        print(f"  {player['player_name']} ({player['position']})")
    
    print(f"\nTotal roster size: {len(your_roster)}")
    print(f"Players with value data: {len(your_team_data)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()