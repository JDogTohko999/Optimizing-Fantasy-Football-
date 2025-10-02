#!/usr/bin/env python3
"""
Debug script to see what team data ESPN is returning
"""
import fantasy_config as config
from espn_client import ESPNClient
import json

try:
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    
    # Get raw team data to debug
    print("Making raw API request to ESPN...")
    
    params = {'view': 'mTeam'}
    data = espn._make_request(params)
    
    if data:
        print("Raw ESPN API Response (teams section):")
        if 'teams' in data:
            print(f"Found {len(data['teams'])} teams")
            for i, team in enumerate(data['teams'], 1):
                print(f"\nTeam {i}:")
                print(f"  Raw team data keys: {list(team.keys())}")
                
                # Try different possible name fields
                possible_names = ['name', 'teamName', 'location', 'nickname']
                for name_field in possible_names:
                    if name_field in team:
                        print(f"  {name_field}: '{team[name_field]}'")
                
                # Check if name is nested
                if 'teamInfo' in team:
                    print(f"  teamInfo: {team['teamInfo']}")
                
                # Show record
                if 'record' in team:
                    record = team['record']['overall']
                    print(f"  Record: {record['wins']}-{record['losses']}")
                
                if i > 3:  # Just show first few for debugging
                    print("  ... (showing first 3 teams only)")
                    break
        else:
            print("No 'teams' field found in response")
            print(f"Available fields: {list(data.keys())}")
    else:
        print("No data returned from ESPN API")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()