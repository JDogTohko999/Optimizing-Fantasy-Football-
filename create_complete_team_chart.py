#!/usr/bin/env python3
"""
Create a bar graph showing the sum of ALL player market values from each team
"""
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

print("="*80)
print("CREATING COMPLETE TEAM VALUE COMPARISON BAR CHART")
print("="*80)

try:
    # Get all rosters and teams
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    teams_df = espn.get_all_teams()
    rosters_df = espn.get_all_rosters()
    
    # Merge team info with rosters
    rosters_df = rosters_df.merge(teams_df[['team_id', 'wins', 'losses', 'points_for']], on='team_id', how='left')
    
    # Get FantasyCalc market values
    print("Fetching FantasyCalc market values...")
    perceived_df = get_perceived_values()
    
    # Merge rosters with market values
    merged_df = rosters_df.merge(perceived_df[['player_name', 'perceived_value']], on='player_name', how='left')
    
    # Calculate ALL player values for each team
    team_values = []
    
    print(f"\nCalculating COMPLETE roster values for each team...")
    
    for team_name in teams_df['team_name'].unique():
        team_players = merged_df[merged_df['team_name'] == team_name].copy()
        
        # Get ALL players on roster
        total_roster_size = len(team_players)
        
        # Get players with market values
        valued_players = team_players.dropna(subset=['perceived_value'])
        
        # Calculate total value of ALL valued players
        total_value = valued_players['perceived_value'].sum()
        
        # Get team record
        team_info = teams_df[teams_df['team_name'] == team_name].iloc[0]
        wins = team_info['wins']
        losses = team_info['losses']
        points_for = team_info['points_for']
        
        team_values.append({
            'team_name': team_name,
            'total_value': total_value,
            'total_roster_size': total_roster_size,
            'valued_players': len(valued_players),
            'coverage_pct': len(valued_players) / total_roster_size * 100,
            'wins': wins,
            'losses': losses,
            'points_for': points_for,
            'record': f"{wins}-{losses}"
        })
        
        print(f"  {team_name:<30} Total Value: ${total_value:>8,.0f} ({len(valued_players)}/{total_roster_size} players = {len(valued_players)/total_roster_size*100:.1f}%)")
    
    # Convert to DataFrame and sort by value
    team_values_df = pd.DataFrame(team_values).sort_values('total_value', ascending=True)
    
    # Create the bar chart
    plt.figure(figsize=(15, 12))
    
    # Create colors based on coverage percentage (how many players have value data)
    colors = plt.cm.viridis(team_values_df['coverage_pct'] / 100)
    
    # Create horizontal bar chart
    bars = plt.barh(range(len(team_values_df)), team_values_df['total_value'], color=colors)
    
    # Customize the chart
    plt.title('Fantasy League Complete Roster Value\nSum of ALL Players with Market Values (FantasyCalc)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Total Market Value ($)', fontsize=12, fontweight='bold')
    plt.ylabel('Teams', fontsize=12, fontweight='bold')
    
    # Set y-axis labels with team names, records, and coverage
    team_labels = [f"{row['team_name']} ({row['record']}) - {row['valued_players']}/{row['total_roster_size']} players" 
                   for _, row in team_values_df.iterrows()]
    plt.yticks(range(len(team_values_df)), team_labels, fontsize=10)
    
    # Add value labels on bars
    for i, (_, row) in enumerate(team_values_df.iterrows()):
        value = row['total_value']
        plt.text(value + 500, i, f'${value:,.0f}', 
                va='center', ha='left', fontweight='bold', fontsize=10)
    
    # Add grid for easier reading
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Highlight your team
    your_team = "Quinshon Judkins"
    your_team_idx = team_values_df[team_values_df['team_name'] == your_team].index
    if not your_team_idx.empty:
        idx = list(team_values_df.index).index(your_team_idx[0])
        bars[idx].set_edgecolor('gold')
        bars[idx].set_linewidth(4)
        
        # Add arrow pointing to your team
        your_value = team_values_df.loc[your_team_idx[0], 'total_value']
        plt.annotate('← YOUR TEAM', 
                    xy=(your_value, idx), 
                    xytext=(your_value + 3000, idx),
                    arrowprops=dict(arrowstyle='->', color='gold', lw=3),
                    fontsize=14, fontweight='bold', color='darkorange')
    
    # Add color bar legend for coverage percentage
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=100))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca(), orientation='vertical', pad=0.01, shrink=0.8)
    cbar.set_label('Player Coverage %', rotation=270, labelpad=15, fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the chart
    output_file = 'output/complete_team_values_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    print(f"\n📊 Complete roster bar chart saved to: {output_file}")
    
    # Show the chart
    plt.show()
    
    # Print summary statistics
    print(f"\n📈 COMPLETE TEAM VALUE SUMMARY:")
    print("="*70)
    highest_team = team_values_df.iloc[-1]
    lowest_team = team_values_df.iloc[0]
    
    print(f"Highest value team: {highest_team['team_name']} (${highest_team['total_value']:,.0f})")
    print(f"Lowest value team:  {lowest_team['team_name']} (${lowest_team['total_value']:,.0f})")
    print(f"Average team value: ${team_values_df['total_value'].mean():,.0f}")
    print(f"Value spread:       ${highest_team['total_value'] - lowest_team['total_value']:,.0f}")
    
    # Find your team's position
    your_team_data = team_values_df[team_values_df['team_name'] == your_team].iloc[0]
    your_rank = len(team_values_df) - list(team_values_df['team_name']).index(your_team)
    
    print(f"\nYour team rank:     #{your_rank} out of {len(team_values_df)}")
    print(f"Your team value:    ${your_team_data['total_value']:,.0f}")
    print(f"Your coverage:      {your_team_data['valued_players']}/{your_team_data['total_roster_size']} players ({your_team_data['coverage_pct']:.1f}%)")
    
    # Show correlation analysis
    win_correlation = team_values_df['total_value'].corr(team_values_df['wins'])
    points_correlation = team_values_df['total_value'].corr(team_values_df['points_for'])
    
    print(f"\nValue-Wins correlation:   {win_correlation:.3f}")
    print(f"Value-Points correlation: {points_correlation:.3f}")
    
    print(f"\n🏆 COMPLETE ROSTER VALUE RANKINGS:")
    print("-"*70)
    for i, (_, row) in enumerate(team_values_df.tail().iterrows(), len(team_values_df)-4):
        marker = "👑" if row['team_name'] == your_team else "  "
        print(f"{i}. {row['team_name']:<25} ${row['total_value']:>8,.0f} ({row['valued_players']}/{row['total_roster_size']} players) {marker}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()