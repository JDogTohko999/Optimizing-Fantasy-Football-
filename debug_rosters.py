#!/usr/bin/env python3
"""
Debug script to check roster data with team names
"""
import fantasy_config as config
from espn_client import ESPNClient

try:
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    
    print("Getting roster data...")
    rosters_df = espn.get_all_rosters()
    
    print(f"\nRoster DataFrame shape: {rosters_df.shape}")
    print(f"Columns: {list(rosters_df.columns)}")
    
    print(f"\nFirst 5 roster entries:")
    print(rosters_df[['player_name', 'team_name', 'team_id', 'position']].head())
    
    print(f"\nUnique team names in roster data:")
    print(rosters_df['team_name'].unique())
    
    print(f"\nUnique team IDs in roster data:")
    print(sorted(rosters_df['team_id'].unique()))
    
    # Check if your team's players are there
    quinshon_team_id = None
    teams_df = espn.get_all_teams()
    for _, team in teams_df.iterrows():
        if team['team_name'] == 'Quinshon Judkins':
            quinshon_team_id = team['team_id']
            break
    
    if quinshon_team_id:
        print(f"\nYour team ID: {quinshon_team_id}")
        your_players = rosters_df[rosters_df['team_id'] == quinshon_team_id]
        print(f"Your players count: {len(your_players)}")
        print("Your players:")
        print(your_players[['player_name', 'position']].head(10))
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()