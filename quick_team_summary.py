#!/usr/bin/env python3
"""
Quick summary table of team values
"""
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values
import pandas as pd

try:
    # Get data
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    teams_df = espn.get_all_teams()
    rosters_df = espn.get_all_rosters()
    rosters_df = rosters_df.merge(teams_df[['team_id', 'wins', 'losses']], on='team_id', how='left')
    
    perceived_df = get_perceived_values()
    merged_df = rosters_df.merge(perceived_df[['player_name', 'perceived_value']], on='player_name', how='left')
    
    # Calculate team values
    team_summary = []
    for team_name in teams_df['team_name'].unique():
        team_players = merged_df[merged_df['team_name'] == team_name]
        valued_players = team_players.dropna(subset=['perceived_value']).sort_values('perceived_value', ascending=False)
        
        top_8_value = valued_players.head(8)['perceived_value'].sum()
        team_info = teams_df[teams_df['team_name'] == team_name].iloc[0]
        
        team_summary.append({
            'Team': team_name,
            'Record': f"{team_info['wins']}-{team_info['losses']}",
            'Top_8_Value': top_8_value,
            'Wins': team_info['wins']
        })
    
    # Sort and display
    df = pd.DataFrame(team_summary).sort_values('Top_8_Value', ascending=False)
    
    print("🏆 LEAGUE TEAM VALUES - TOP 8 PLAYERS")
    print("="*60)
    print(f"{'Rank':<4} {'Team':<30} {'Record':<8} {'Top 8 Value':<12}")
    print("-"*60)
    
    for i, (_, row) in enumerate(df.iterrows(), 1):
        marker = "👑" if row['Team'] == "Quinshon Judkins" else "  "
        print(f"{i:<4} {row['Team']:<30} {row['Record']:<8} ${row['Top_8_Value']:<11,.0f} {marker}")
    
    print("-"*60)
    your_rank = df[df['Team'] == "Quinshon Judkins"].index[0] + 1
    print(f"Your team (Quinshon Judkins) ranks #{your_rank} out of {len(df)} teams!")
    
except Exception as e:
    print(f"Error: {e}")