#!/usr/bin/env python3
"""
Simple script to show all teams in your league with clear numbers
"""
import fantasy_config as config
from espn_client import ESPNClient

print("="*60)
print("YOUR FANTASY LEAGUE TEAMS")
print("="*60)

try:
    # Connect to ESPN
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    
    # Get league info
    league_info = espn.get_league_info()
    if league_info:
        print(f"League: {league_info['name']}")
        print(f"Size: {league_info['size']} teams")
        print("")
    
    # Get all teams
    teams_df = espn.get_all_teams()
    
    if teams_df.empty:
        print("❌ No teams found - check your ESPN_S2 and SWID cookies")
    else:
        print("TEAM LIST:")
        print("-" * 60)
        
        for i, (_, team) in enumerate(teams_df.iterrows(), 1):
            team_name = team.get('team_name', 'Unknown Team')
            wins = team.get('wins', 0)
            losses = team.get('losses', 0)
            points = team.get('points_for', 0)
            
            print(f"{i:2}. {team_name:<35} ({wins}-{losses}, {points:.1f} PF)")
        
        print("-" * 60)
        print(f"\nTo use the optimizer:")
        print(f"1. Remember YOUR team number from the list above")
        print(f"2. Run: python main.py")
        print(f"3. Enter your team number when prompted")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nThis might happen if:")
    print("- Your ESPN_S2 and SWID cookies are expired")
    print("- The league is private and you need fresh cookies")
    print("- There's a network issue")