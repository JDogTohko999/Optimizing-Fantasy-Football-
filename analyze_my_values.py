#!/usr/bin/env python3
"""
Show your team analysis using just FantasyCalc data (no ESPN projections needed)
"""
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values
import pandas as pd

print("="*80)
print("YOUR TEAM ANALYSIS - FANTASYCALC VALUES ONLY")
print("="*80)

try:
    # Get your roster
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    rosters_df = espn.get_all_rosters()
    
    your_team = "Quinshon Judkins"
    your_roster = rosters_df[rosters_df['team_name'] == your_team]
    
    # Get FantasyCalc data
    perceived_df = get_perceived_values()
    
    # Merge your roster with FantasyCalc values
    merged = your_roster.merge(perceived_df[['player_name', 'perceived_value', 'overall_rank', 'position_rank']], 
                              on='player_name', how='left')
    
    # Get only players with values
    valued_players = merged.dropna(subset=['perceived_value']).sort_values('perceived_value', ascending=False)
    
    print(f"📊 YOUR QUINSHON JUDKINS ROSTER BY MARKET VALUE")
    print("="*80)
    print(f"{'Player':<25} {'Pos':<8} {'Market Value':<12} {'Overall Rank':<12} {'Pos Rank'}")
    print("-"*80)
    
    total_value = 0
    for _, player in valued_players.iterrows():
        value = int(player['perceived_value'])
        total_value += value
        overall_rank = int(player['overall_rank']) if pd.notna(player['overall_rank']) else 999
        pos_rank = int(player['position_rank']) if pd.notna(player['position_rank']) else 999
        
        print(f"{player['player_name']:<25} {player['position']:<8} {value:<12,} #{overall_rank:<11} #{pos_rank}")
    
    print("-"*80)
    print(f"{'TOTAL MARKET VALUE:':<33} {total_value:,}")
    print(f"{'PLAYERS WITH VALUE DATA:':<33} {len(valued_players)}/{len(your_roster)}")
    
    # Show players without FantasyCalc data
    unvalued_players = merged[merged['perceived_value'].isna()]
    if not unvalued_players.empty:
        print(f"\n❌ PLAYERS WITHOUT FANTASYCALC DATA:")
        print("-"*50)
        for _, player in unvalued_players.iterrows():
            print(f"  {player['player_name']} ({player['position']})")
    
    # League comparison (rough estimate)
    print(f"\n📈 TEAM VALUE ANALYSIS:")
    print("-"*50)
    avg_team_value = total_value  # Your team value as baseline
    
    # Calculate percentile based on your top players
    top_3_value = valued_players.head(3)['perceived_value'].sum()
    
    print(f"Your team total value: {total_value:,}")
    print(f"Top 3 players value:   {int(top_3_value):,} ({top_3_value/total_value*100:.1f}%)")
    print(f"Average per player:    {total_value/len(valued_players):,.0f}")
    
    # Show tier analysis
    print(f"\n🏆 PLAYER TIERS ON YOUR TEAM:")
    print("-"*50)
    
    for _, player in valued_players.iterrows():
        value = player['perceived_value']
        name = player['player_name']
        
        if value >= 5000:
            tier = "🔥 Elite (Top Tier)"
        elif value >= 2000:
            tier = "⭐ High Value"
        elif value >= 1000:
            tier = "💪 Solid Starter"
        elif value >= 500:
            tier = "📈 Depth/Upside"
        else:
            tier = "🆗 Bench/Handcuff"
        
        print(f"  {name:<25} {tier}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()