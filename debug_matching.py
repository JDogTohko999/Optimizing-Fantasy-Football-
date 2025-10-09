#!/usr/bin/env python3
"""
Debug script to see why only 1 player is being matched
"""
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values
import pandas as pd

print("="*80)
print("DEBUGGING PLAYER MATCHING ISSUES")
print("="*80)

try:
    # Get your roster
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    rosters_df = espn.get_all_rosters()
    
    your_team = "Quinshon Judkins"
    your_roster = rosters_df[rosters_df['team_name'] == your_team]
    
    print(f"YOUR ROSTER ({len(your_roster)} players):")
    print("-" * 50)
    for _, player in your_roster.iterrows():
        print(f"  {player['player_name']} ({player['position']})")
    
    # Get FantasyCalc data
    print(f"\nFETCHING FANTASYCALC DATA...")
    perceived_df = get_perceived_values()
    print(f"FantasyCalc has {len(perceived_df)} players")
    
    # Check which of your players are in FantasyCalc
    print(f"\nCHECKING YOUR PLAYERS IN FANTASYCALC:")
    print("-" * 80)
    found_count = 0
    
    for _, player in your_roster.iterrows():
        espn_name = player['player_name']
        
        # Check exact match
        exact_match = perceived_df[perceived_df['player_name'] == espn_name]
        
        if not exact_match.empty:
            found_count += 1
            fc_player = exact_match.iloc[0]
            print(f"✅ {espn_name:<25} -> Found: {fc_player['player_name']} (Value: {fc_player['perceived_value']})")
        else:
            # Check for partial matches
            partial_matches = perceived_df[perceived_df['player_name'].str.contains(espn_name.split()[0], case=False, na=False)]
            if not partial_matches.empty:
                print(f"⚠️  {espn_name:<25} -> Partial matches:")
                for _, match in partial_matches.head(3).iterrows():
                    print(f"     -> {match['player_name']} ({match['position']})")
            else:
                print(f"❌ {espn_name:<25} -> Not found in FantasyCalc")
    
    print(f"\nMATCH SUMMARY:")
    print(f"  Your roster: {len(your_roster)} players")
    print(f"  Exact matches: {found_count} players")
    print(f"  Missing: {len(your_roster) - found_count} players")
    
    # Get ESPN projections
    print(f"\nCHECKING ESPN PROJECTIONS:")
    print("-" * 50)
    projections_df = espn.get_rest_of_season_projections()
    print(f"ESPN projections has {len(projections_df)} players")
    
    if not projections_df.empty:
        print("Sample projection players:")
        for _, player in projections_df.head(10).iterrows():
            print(f"  {player['player_name']} -> {player.get('rest_of_season_projection', 'N/A')}")
    
    # Check your players in projections
    proj_found = 0
    for _, player in your_roster.iterrows():
        espn_name = player['player_name']
        proj_match = projections_df[projections_df['player_name'] == espn_name] if not projections_df.empty else pd.DataFrame()
        
        if not proj_match.empty:
            proj_found += 1
    
    print(f"\nPROJECTION MATCHES:")
    print(f"  Your roster: {len(your_roster)} players")
    print(f"  In projections: {proj_found} players")
    
    # Show the actual matching process
    print(f"\nDETAILED MATCHING PROCESS:")
    print("-" * 80)
    
    # Merge step by step like the analyzer does
    step1 = your_roster.merge(perceived_df[['player_name', 'perceived_value']], on='player_name', how='left')
    step1_matches = step1['perceived_value'].notna().sum()
    print(f"Step 1 - After merging perceived values: {step1_matches} matches")
    
    if not projections_df.empty:
        step2 = step1.merge(projections_df[['player_name', 'rest_of_season_projection']], on='player_name', how='left')
        step2_matches = step2[['perceived_value', 'rest_of_season_projection']].notna().all(axis=1).sum()
        print(f"Step 2 - After merging projections: {step2_matches} matches")
        
        print(f"\nFINAL MATCHED PLAYERS:")
        final_matches = step2.dropna(subset=['perceived_value', 'rest_of_season_projection'])
        for _, player in final_matches.iterrows():
            print(f"  ✅ {player['player_name']} - Perceived: {player['perceived_value']}, Projected: {player['rest_of_season_projection']}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()