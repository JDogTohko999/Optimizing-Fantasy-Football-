#!/usr/bin/env python3
"""
Debug script to test Fantasy Trade Optimizer
"""
import os
import sys
import traceback

print("="*60)
print("FANTASY TRADE OPTIMIZER - DEBUG MODE")
print("="*60)

try:
    print("1. Testing environment...")
    from dotenv import load_dotenv
    load_dotenv()
    print(f"   ✓ League ID: {os.getenv('LEAGUE_ID')}")
    print(f"   ✓ Season: {os.getenv('SEASON')}")
    print(f"   ✓ ESPN_S2 length: {len(os.getenv('ESPN_S2', ''))}")
    print(f"   ✓ SWID present: {'Yes' if os.getenv('SWID') else 'No'}")
    
    print("\n2. Testing config import...")
    import fantasy_config as config
    print(f"   ✓ Config loaded")
    print(f"   ✓ League ID: {config.LEAGUE_ID}")
    print(f"   ✓ Season: {config.SEASON}")
    
    print("\n3. Testing ESPN client import...")
    from espn_client import ESPNClient
    print("   ✓ ESPNClient imported successfully")
    
    print("\n4. Testing ESPN connection...")
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    league_info = espn.get_league_info()
    
    if league_info:
        print(f"   ✓ Connected to league: {league_info.get('name', 'Unknown')}")
        print(f"   ✓ League size: {league_info.get('size', 'Unknown')} teams")
    else:
        print("   ✗ Failed to connect to ESPN league")
        print("   Note: This might be because Week 4 data isn't fully available yet")
        
    print("\n5. Testing value sources...")
    from value_sources import get_perceived_values
    print("   ✓ Value sources imported")
    
    print("\n6. Testing perceived values...")
    perceived_df = get_perceived_values()
    if not perceived_df.empty:
        print(f"   ✓ Got perceived values for {len(perceived_df)} players")
        print(f"   Top 5 players by value:")
        top_players = perceived_df.nlargest(5, 'perceived_value')[['player_name', 'position', 'perceived_value']]
        for _, player in top_players.iterrows():
            print(f"     {player['player_name']} ({player['position']}): {player['perceived_value']}")
    else:
        print("   ✗ No perceived values retrieved")
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE - Ready to run full analysis!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)