"""
ESPN Fantasy Football Trade Optimizer
Main execution script - REDRAFT LEAGUE OPTIMIZED

Usage:
    python main.py
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Import our modules
import fantasy_config as config
from espn_client import ESPNClient
from value_sources import get_perceived_values, get_forecasted_values, combine_recent_performance_with_projections
from trade_analyzer import TradeAnalyzer, TradeReporter

def setup_output_directory():
    """Create output directory if it doesn't exist"""
    Path(config.OUTPUT_DIR).mkdir(exist_ok=True)

def select_team(teams_df: pd.DataFrame) -> str:
    """Interactive team selection"""
    print("\n" + "="*80)
    print("TEAMS IN YOUR LEAGUE")
    print("="*80)
    
    teams = teams_df['team_name'].unique()
    for i, team in enumerate(teams, 1):
        team_info = teams_df[teams_df['team_name'] == team].iloc[0]
        print(f"{i:2}. {team:40} ({team_info['wins']}-{team_info['losses']}, {team_info['points_for']:.1f} PF)")
    
    while True:
        try:
            choice = input("\nEnter the number of YOUR team: ")
            team_num = int(choice) - 1
            if 0 <= team_num < len(teams):
                return teams[team_num]
            else:
                print(f"Please enter a number between 1 and {len(teams)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

def export_results(analyzer: TradeAnalyzer, suggestions: pd.DataFrame, your_team: str):
    """Export analysis results to files"""
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    if config.EXPORT_CSV:
        # Export full analysis
        filename = f"{config.OUTPUT_DIR}/trade_analysis_{config.LEAGUE_ID}_{timestamp}.csv"
        analyzer.merged_df.to_csv(filename, index=False)
        print(f"\n✓ Full analysis exported to: {filename}")
        
        # Export trade suggestions
        if not suggestions.empty:
            suggestions_file = f"{config.OUTPUT_DIR}/trade_suggestions_{config.LEAGUE_ID}_{timestamp}.csv"
            suggestions.to_csv(suggestions_file, index=False)
            print(f"✓ Trade suggestions exported to: {suggestions_file}")
    
    if config.EXPORT_JSON:
        json_file = f"{config.OUTPUT_DIR}/trade_analysis_{config.LEAGUE_ID}_{timestamp}.json"
        analyzer.merged_df.to_json(json_file, orient='records', indent=2)
        print(f"✓ JSON export saved to: {json_file}")

def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("ESPN FANTASY FOOTBALL TRADE OPTIMIZER")
    print("REDRAFT LEAGUE EDITION")
    print("="*80)
    
    # Validate configuration
    try:
        config.validate_config()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure all required values are set.")
        sys.exit(1)
    
    setup_output_directory()
    
    # Step 1: Connect to ESPN and fetch league data
    print(f"\n{'='*80}")
    print("STEP 1: FETCHING ESPN LEAGUE DATA")
    print("="*80)
    
    espn = ESPNClient(config.LEAGUE_ID, config.SEASON)
    
    # Get league info
    league_info = espn.get_league_info()
    if league_info:
        print(f"\n✓ Connected to league: {league_info['name']}")
        print(f"  League size: {league_info['size']} teams")
    else:
        print("\n❌ Failed to connect to ESPN league")
        print("If this is a private league, make sure ESPN_S2 and SWID are set in .env")
        sys.exit(1)
    
    # Get all teams
    teams_df = espn.get_all_teams()
    print(f"✓ Loaded {len(teams_df)} teams")
    
    # Get all rosters
    rosters_df = espn.get_all_rosters()
    print(f"✓ Loaded {len(rosters_df)} rostered players")
    
    # Merge team info with rosters
    rosters_df = rosters_df.merge(teams_df[['team_id', 'wins', 'losses']], on='team_id', how='left')
    
    # Select your team
    if config.YOUR_TEAM_NAME:
        your_team = config.YOUR_TEAM_NAME
        if your_team not in rosters_df['team_name'].values:
            print(f"\n⚠ Team '{your_team}' not found in league")
            your_team = select_team(teams_df)
    else:
        your_team = select_team(teams_df)
    
    print(f"\n✓ Analyzing trades for: {your_team}")
    
    # Step 2: Get perceived values (market value)
    print(f"\n{'='*80}")
    print("STEP 2: FETCHING PERCEIVED VALUES (Market Trade Values)")
    print("="*80)
    
    perceived_df = get_perceived_values()
    
    if perceived_df.empty:
        print("\n❌ Failed to fetch perceived values")
        print("Cannot proceed without market value data")
        sys.exit(1)
    
    # Step 3: Get forecasted values (rest of season projections)
    print(f"\n{'='*80}")
    print("STEP 3: FETCHING FORECASTED VALUES (Rest of Season Projections)")
    print("="*80)
    
    espn_projections = espn.get_rest_of_season_projections()
    
    if espn_projections.empty:
        print("⚠ No ESPN projections available")
        forecasted_df = pd.DataFrame()
    else:
        print(f"✓ Loaded projections for {len(espn_projections)} players")
        
        # Optionally combine with recent performance
        recent_stats = espn.get_player_stats_last_4_weeks()
        if not recent_stats.empty:
            print(f"✓ Loaded recent stats for {len(recent_stats)} players")
            forecasted_df = combine_recent_performance_with_projections(
                espn_projections,
                recent_stats,
                weight_recent=config.RECENT_GAMES_WEIGHT
            )
        else:
            forecasted_df = espn_projections
    
    if forecasted_df.empty:
        forecasted_df = get_forecasted_values()
    
    if forecasted_df.empty:
        print("\n❌ Failed to fetch forecasted values")
        print("Cannot proceed without projection data")
        sys.exit(1)
    
    # Step 4: Analyze trades
    print(f"\n{'='*80}")
    print("STEP 4: ANALYZING TRADES")
    print("="*80)
    
    analyzer = TradeAnalyzer(rosters_df, perceived_df, forecasted_df)
    
    # Merge data sources
    merged_df = analyzer.merge_data_sources()
    
    if merged_df.empty:
        print("\n❌ No players with complete data")
        print("Check that player names match between ESPN and value sources")
        sys.exit(1)
    
    # Normalize values
    analyzer.normalize_values()
    
    # Calculate discount/premium
    analyzer.calculate_discount_premium()
    
    # Step 5: Generate reports
    print(f"\n{'='*80}")
    print("STEP 5: GENERATING TRADE RECOMMENDATIONS")
    print("="*80)
    
    # Analyze your team
    your_overvalued, your_undervalued = analyzer.analyze_team(your_team)
    
    reporter = TradeReporter()
    
    # Show complete roster analysis first
    your_team_data = analyzer.get_team_data(your_team)
    reporter.print_full_team_ratios(your_team, your_team_data)
    
    # Then show the focused over/undervalued analysis
    reporter.print_team_analysis(your_team, your_overvalued, your_undervalued)
    
    # Find trade targets
    trade_targets = analyzer.find_trade_targets(your_team)
    reporter.print_trade_targets(trade_targets)
    
    # Suggest specific trades
    trade_suggestions = analyzer.suggest_trade_pairs(your_team, max_suggestions=10)
    reporter.print_trade_suggestions(trade_suggestions)
    
    # Print summary
    stats = analyzer.get_summary_stats()
    reporter.print_summary(stats)
    
    # Step 6: Export results
    print(f"\n{'='*80}")
    print("STEP 6: EXPORTING RESULTS")
    print("="*80)
    
    export_results(analyzer, trade_suggestions, your_team)
    
    # Final message
    print(f"\n{'='*80}")
    print("✅ ANALYSIS COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the trade suggestions above")
    print("2. Check the exported CSV files in the 'output' directory")
    print("3. Consider team needs and roster construction")
    print("4. Reach out to other managers with trade offers!")
    print("\nTip: Trades that look 'fair' to the market but give you")
    print("     forecasted value are the sweet spot!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)