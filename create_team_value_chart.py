#!/usr/bin/env python3
"""
Create a bar graph showing the sum of top 8 market value players from each team
"""
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

print("="*80)
print("CREATING TEAM VALUE COMPARISON BAR CHART")
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
    
    # Calculate top 8 player values for each team
    team_values = []
    
    print(f"\nCalculating top 8 player values for each team...")
    
    for team_name in teams_df['team_name'].unique():
        team_players = merged_df[merged_df['team_name'] == team_name].copy()
        
        # Get players with market values and sort by value
        valued_players = team_players.dropna(subset=['perceived_value']).sort_values('perceived_value', ascending=False)
        
        # Take top 8 players (typical starting lineup)
        top_8 = valued_players.head(8)
        total_value = top_8['perceived_value'].sum()
        
        # Get team record
        team_info = teams_df[teams_df['team_name'] == team_name].iloc[0]
        wins = team_info['wins']
        losses = team_info['losses']
        points_for = team_info['points_for']
        
        team_values.append({
            'team_name': team_name,
            'top_8_value': total_value,
            'players_counted': len(top_8),
            'wins': wins,
            'losses': losses,
            'points_for': points_for,
            'record': f"{wins}-{losses}"
        })
        
        print(f"  {team_name:<30} Top 8 Value: ${total_value:>8,.0f} ({len(top_8)} players with data)")
    
    # Convert to DataFrame and sort by value
    team_values_df = pd.DataFrame(team_values).sort_values('top_8_value', ascending=True)
    
    # Create the bar chart
    plt.figure(figsize=(14, 10))
    
    # Create colors based on record (wins)
    colors = plt.cm.RdYlGn(team_values_df['wins'] / team_values_df['wins'].max())
    
    # Create horizontal bar chart
    bars = plt.barh(range(len(team_values_df)), team_values_df['top_8_value'], color=colors)
    
    # Customize the chart
    plt.title('Fantasy League Team Strength\nSum of Top 8 Player Market Values (FantasyCalc)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Total Market Value ($)', fontsize=12, fontweight='bold')
    plt.ylabel('Teams', fontsize=12, fontweight='bold')
    
    # Set y-axis labels with team names and records
    team_labels = [f"{row['team_name']} ({row['record']})" for _, row in team_values_df.iterrows()]
    plt.yticks(range(len(team_values_df)), team_labels)
    
    # Add value labels on bars
    for i, (_, row) in enumerate(team_values_df.iterrows()):
        value = row['top_8_value']
        plt.text(value + 500, i, f'${value:,.0f}', 
                va='center', ha='left', fontweight='bold', fontsize=9)
    
    # Add grid for easier reading
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    
    # Highlight your team
    your_team = "Quinshon Judkins"
    your_team_idx = team_values_df[team_values_df['team_name'] == your_team].index
    if not your_team_idx.empty:
        idx = list(team_values_df.index).index(your_team_idx[0])
        bars[idx].set_edgecolor('gold')
        bars[idx].set_linewidth(3)
        
        # Add arrow pointing to your team
        your_value = team_values_df.loc[your_team_idx[0], 'top_8_value']
        plt.annotate('← YOUR TEAM', 
                    xy=(your_value, idx), 
                    xytext=(your_value + 3000, idx),
                    arrowprops=dict(arrowstyle='->', color='gold', lw=2),
                    fontsize=12, fontweight='bold', color='darkorange')
    
    # Add color bar legend for wins
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn, norm=plt.Normalize(vmin=0, vmax=team_values_df['wins'].max()))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca(), orientation='vertical', pad=0.01, shrink=0.8)
    cbar.set_label('Wins', rotation=270, labelpad=15, fontweight='bold')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the chart
    output_file = 'output/team_values_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    print(f"\n📊 Bar chart saved to: {output_file}")
    
    # Show the chart
    plt.show()
    
    # Print summary statistics
    print(f"\n📈 TEAM VALUE SUMMARY:")
    print("="*60)
    print(f"Highest value team: {team_values_df.iloc[-1]['team_name']} (${team_values_df.iloc[-1]['top_8_value']:,.0f})")
    print(f"Lowest value team:  {team_values_df.iloc[0]['team_name']} (${team_values_df.iloc[0]['top_8_value']:,.0f})")
    print(f"Average team value: ${team_values_df['top_8_value'].mean():,.0f}")
    print(f"Your team rank:     #{len(team_values_df) - list(team_values_df['team_name']).index(your_team)} out of {len(team_values_df)}")
    
    # Show correlation with wins
    correlation = team_values_df['top_8_value'].corr(team_values_df['wins'])
    print(f"Value-Wins correlation: {correlation:.3f}")
    
    print(f"\n🏆 TOP 5 MOST VALUABLE TEAMS:")
    print("-"*60)
    for i, (_, row) in enumerate(team_values_df.tail(5).iterrows(), 1):
        print(f"{i}. {row['team_name']:<25} ${row['top_8_value']:>8,.0f} ({row['record']})")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()