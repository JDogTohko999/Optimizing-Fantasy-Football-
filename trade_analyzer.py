"""
Trade Analysis Engine
Implements the Reddit methodology for finding optimal trades
Optimized for REDRAFT leagues
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
import fantasy_config as config

class TradeAnalyzer:
    """
    Analyzes trade opportunities using perceived vs forecasted value methodology
    """
    
    def __init__(self, roster_df: pd.DataFrame, perceived_df: pd.DataFrame, forecasted_df: pd.DataFrame):
        self.roster_df = roster_df
        self.perceived_df = perceived_df
        self.forecasted_df = forecasted_df
        self.merged_df = None
    
    def merge_data_sources(self) -> pd.DataFrame:
        """
        Merge roster, perceived value, and forecasted value data
        """
        print("\n" + "="*80)
        print("MERGING DATA SOURCES")
        print("="*80)
        
        # Start with roster
        df = self.roster_df.copy()
        print(f"Roster players: {len(df)}")
        
        # Merge perceived values
        df = df.merge(
            self.perceived_df[['player_name', 'perceived_value', 'perceived_value_adjusted', 'overall_rank']],
            on='player_name',
            how='left'
        )
        print(f"After merging perceived values: {df['perceived_value'].notna().sum()} players matched")
        
        # Merge forecasted values
        # Handle different column names from ESPN projections
        forecast_cols = ['player_name']
        if 'rest_of_season_projection' in self.forecasted_df.columns:
            forecast_cols.append('rest_of_season_projection')
            df = df.merge(
                self.forecasted_df[forecast_cols],
                on='player_name',
                how='left'
            )
            df.rename(columns={'rest_of_season_projection': 'forecasted_value'}, inplace=True)
        elif 'forecasted_value' in self.forecasted_df.columns:
            forecast_cols.append('forecasted_value')
            df = df.merge(
                self.forecasted_df[forecast_cols],
                on='player_name',
                how='left'
            )
        
        print(f"After merging forecasted values: {df['forecasted_value'].notna().sum()} players matched")
        
        # Remove players without both values
        df = df.dropna(subset=['perceived_value', 'forecasted_value'])
        print(f"Final players with complete data: {len(df)}")
        
        # Use adjusted perceived value if available
        if 'perceived_value_adjusted' in df.columns:
            df['perceived_value'] = df['perceived_value_adjusted']
        
        self.merged_df = df
        return df
    
    def normalize_values(self) -> pd.DataFrame:
        """
        Normalize values to percentage of average (Reddit methodology)
        This allows cross-positional comparison
        """
        print("\nNormalizing values...")
        
        df = self.merged_df.copy()
        
        # Calculate averages (only for rostered players to avoid zeros)
        avg_perceived = df['perceived_value'].mean()
        avg_forecasted = df['forecasted_value'].mean()
        
        print(f"Average perceived value: {avg_perceived:.2f}")
        print(f"Average forecasted value: {avg_forecasted:.2f}")
        
        # Normalize to percentage of average (Reddit formula)
        df['perceived_normalized'] = (df['perceived_value'] / avg_perceived) * 100
        df['forecasted_normalized'] = (df['forecasted_value'] / avg_forecasted) * 100
        
        self.merged_df = df
        return df
    
    def calculate_discount_premium(self) -> pd.DataFrame:
        """
        Calculate discount/premium using Reddit formula:
        discount_premium = (forecasted - perceived) / forecasted * 100
        
        Positive % = Undervalued (good to trade FOR)
        Negative % = Overvalued (good to trade AWAY)
        """
        print("\nCalculating discount/premium...")
        
        df = self.merged_df.copy()
        
        # Reddit formula
        df['discount_premium'] = (
            (df['forecasted_normalized'] - df['perceived_normalized']) / 
            df['forecasted_normalized'] * 100
        )
        
        # Categorize
        df['value_category'] = df['discount_premium'].apply(
            lambda x: 'Undervalued' if x > config.MIN_DISCOUNT_THRESHOLD 
            else 'Overvalued' if x < config.MIN_PREMIUM_THRESHOLD 
            else 'Fair Value'
        )
        
        # Add interpretation
        df['interpretation'] = df['discount_premium'].apply(self._interpret_discount)
        
        self.merged_df = df
        return df
    
    @staticmethod
    def _interpret_discount(value: float) -> str:
        """Interpret what the discount/premium means"""
        if value > 30:
            return "Severely undervalued - BUY"
        elif value > 10:
            return "Undervalued - Good buy target"
        elif value > -10:
            return "Fair value"
        elif value > -30:
            return "Overvalued - Good sell candidate"
        else:
            return "Severely overvalued - SELL"
    
    def analyze_team(self, team_name: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Analyze a specific team's roster
        Returns overvalued and undervalued players
        """
        team_df = self.merged_df[self.merged_df['team_name'] == team_name].copy()
        
        overvalued = team_df[team_df['discount_premium'] < config.MIN_PREMIUM_THRESHOLD].sort_values('discount_premium')
        undervalued = team_df[team_df['discount_premium'] > config.MIN_DISCOUNT_THRESHOLD].sort_values('discount_premium', ascending=False)
        
        return overvalued, undervalued
    
    def get_team_data(self, team_name: str) -> pd.DataFrame:
        """
        Get ALL players for a specific team (not just over/undervalued)
        """
        return self.merged_df[self.merged_df['team_name'] == team_name].copy()
    
    def find_trade_targets(self, your_team: str, position_filter: str = None) -> pd.DataFrame:
        """
        Find undervalued players on OTHER teams
        """
        other_teams = self.merged_df[self.merged_df['team_name'] != your_team].copy()
        
        targets = other_teams[other_teams['discount_premium'] > config.MIN_DISCOUNT_THRESHOLD].copy()
        
        if position_filter:
            targets = targets[targets['position'] == position_filter]
        
        # Remove untouchables
        if config.UNTOUCHABLE_PLAYERS:
            targets = targets[~targets['player_name'].isin(config.UNTOUCHABLE_PLAYERS)]
        
        targets = targets.sort_values('discount_premium', ascending=False)
        
        return targets
    
    def suggest_trade_pairs(self, your_team: str, max_suggestions: int = 10) -> pd.DataFrame:
        """
        Suggest specific trade pairs based on similar perceived values
        This is the key insight: trade similar perceived values but gain forecasted value
        """
        your_overvalued, _ = self.analyze_team(your_team)
        trade_targets = self.find_trade_targets(your_team)
        
        if your_overvalued.empty or trade_targets.empty:
            return pd.DataFrame()
        
        suggestions = []
        
        for _, your_player in your_overvalued.iterrows():
            your_perceived = your_player['perceived_normalized']
            
            # Find players with similar perceived value (within tolerance)
            tolerance = config.VALUE_MATCH_TOLERANCE
            similar = trade_targets[
                (trade_targets['perceived_normalized'] >= your_perceived * (1 - tolerance)) &
                (trade_targets['perceived_normalized'] <= your_perceived * (1 + tolerance))
            ].copy()
            
            for _, target in similar.head(3).iterrows():
                value_gain = target['forecasted_normalized'] - your_player['forecasted_normalized']
                
                # Only suggest if we gain value
                if value_gain > 5:
                    suggestions.append({
                        'give_player': your_player['player_name'],
                        'give_position': your_player['position'],
                        'give_perceived': your_player['perceived_normalized'],
                        'give_forecasted': your_player['forecasted_normalized'],
                        'give_discount': your_player['discount_premium'],
                        'get_player': target['player_name'],
                        'get_position': target['position'],
                        'get_team': target['team_name'],
                        'get_perceived': target['perceived_normalized'],
                        'get_forecasted': target['forecasted_normalized'],
                        'get_discount': target['discount_premium'],
                        'value_gain': value_gain,
                        'value_gain_pct': (value_gain / your_player['forecasted_normalized'] * 100) if your_player['forecasted_normalized'] > 0 else 0
                    })
        
        if not suggestions:
            return pd.DataFrame()
        
        df = pd.DataFrame(suggestions).sort_values('value_gain', ascending=False)
        return df.head(max_suggestions)
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the analysis"""
        df = self.merged_df
        
        return {
            'total_players': len(df),
            'undervalued_count': len(df[df['value_category'] == 'Undervalued']),
            'overvalued_count': len(df[df['value_category'] == 'Overvalued']),
            'fair_value_count': len(df[df['value_category'] == 'Fair Value']),
            'avg_discount_premium': df['discount_premium'].mean(),
            'max_discount': df['discount_premium'].max(),
            'max_premium': df['discount_premium'].min()
        }


class TradeReporter:
    """
    Generates formatted reports of trade analysis
    """
    
    @staticmethod
    def print_team_analysis(team_name: str, overvalued: pd.DataFrame, undervalued: pd.DataFrame):
        """Print analysis for a specific team"""
        print("\n" + "="*80)
        print(f"TEAM ANALYSIS: {team_name}")
        print("="*80)
        
        if not overvalued.empty:
            print(f"\n🔴 OVERVALUED PLAYERS (Good to trade away)")
            print("-"*80)
            for _, player in overvalued.iterrows():
                print(f"{player['player_name']:25} {player['position']:5} | "
                      f"Perceived: {player['perceived_normalized']:6.1f} | "
                      f"Forecasted: {player['forecasted_normalized']:6.1f} | "
                      f"Premium: {player['discount_premium']:6.1f}%")
        else:
            print("\n✓ No significantly overvalued players on your roster")
        
        if not undervalued.empty:
            print(f"\n🟢 UNDERVALUED PLAYERS (Good value on your roster)")
            print("-"*80)
            for _, player in undervalued.iterrows():
                print(f"{player['player_name']:25} {player['position']:5} | "
                      f"Perceived: {player['perceived_normalized']:6.1f} | "
                      f"Forecasted: {player['forecasted_normalized']:6.1f} | "
                      f"Discount: {player['discount_premium']:6.1f}%")
        else:
            print("\n⚠ No significantly undervalued players on your roster")

    @staticmethod
    def print_full_team_ratios(team_name: str, team_df: pd.DataFrame):
        """Print ALL players on team with their discount/premium ratios"""
        print("\n" + "="*80)
        print(f"📊 COMPLETE ROSTER ANALYSIS: {team_name}")
        print("="*80)
        
        if team_df.empty:
            print(f"\n❌ No players found with complete data for {team_name}")
            print("This might mean:")
            print("- Player names don't match between ESPN and FantasyCalc")
            print("- Players are too low-value to be tracked by FantasyCalc")
            return
        
        # Sort by discount/premium (best values first)
        team_sorted = team_df.sort_values('discount_premium', ascending=False)
        
        print(f"\nYour {len(team_sorted)} players with complete value data:")
        print("-"*80)
        print(f"{'Player':25} {'Pos':5} | {'Perceived':>9} | {'Forecast':>9} | {'Ratio':>7} | Status")
        print("-"*80)
        
        for _, player in team_sorted.iterrows():
            ratio = player['discount_premium']
            
            # Color coding for ratio
            if ratio > 20:
                status = "🟢 Great Buy"
            elif ratio > 0:
                status = "🟡 Fair Value"
            elif ratio > -20:
                status = "🟠 Slight Premium"
            else:
                status = "🔴 Overvalued"
            
            print(f"{player['player_name']:25} {player['position']:5} | "
                  f"{player['perceived_normalized']:9.1f} | "
                  f"{player['forecasted_normalized']:9.1f} | "
                  f"{ratio:+6.1f}% | {status}")
        
        # Summary stats for your team
        avg_ratio = team_sorted['discount_premium'].mean()
        best_player = team_sorted.iloc[0]['player_name'] if not team_sorted.empty else "None"
        worst_player = team_sorted.iloc[-1]['player_name'] if not team_sorted.empty else "None"
        
        print("-"*80)
        print(f"Team Summary:")
        print(f"  Average Ratio: {avg_ratio:+.1f}%")
        print(f"  Best Value:    {best_player}")
        print(f"  Worst Value:   {worst_player}")
        print(f"  Players analyzed: {len(team_sorted)}")
        
    @staticmethod
    def print_trade_targets(targets: pd.DataFrame, max_display: int = 15):
        """Print top trade targets"""
        print("\n" + "="*80)
        print("🎯 TOP TRADE TARGETS (Undervalued players on other teams)")
        print("="*80)
        
        if targets.empty:
            print("\nNo undervalued players found on other teams.")
            return
        
        for _, player in targets.head(max_display).iterrows():
            print(f"\n{player['player_name']:25} ({player['position']}) - {player['team_name']}")
            print(f"  Perceived Value: {player['perceived_normalized']:6.1f}")
            print(f"  Forecasted Value: {player['forecasted_normalized']:6.1f}")
            print(f"  Discount: {player['discount_premium']:6.1f}% - {player['interpretation']}")
    
    @staticmethod
    def print_trade_suggestions(suggestions: pd.DataFrame):
        """Print suggested trade pairs"""
        print("\n" + "="*80)
        print("💡 SUGGESTED TRADES (Similar perceived value, gain forecasted value)")
        print("="*80)
        
        if suggestions.empty:
            print("\nNo optimal trade pairs found.")
            print("Try adjusting VALUE_MATCH_TOLERANCE in config.py")
            return
        
        for i, trade in suggestions.iterrows():
            print(f"\n{'='*80}")
            print(f"TRADE #{i+1}")
            print(f"{'='*80}")
            print(f"GIVE: {trade['give_player']:25} ({trade['give_position']})")
            print(f"  └─ Perceived Value: {trade['give_perceived']:6.1f}")
            print(f"  └─ Forecasted Value: {trade['give_forecasted']:6.1f}")
            print(f"  └─ Premium: {trade['give_discount']:6.1f}% (Overvalued)")
            print(f"\nGET:  {trade['get_player']:25} ({trade['get_position']}) from {trade['get_team']}")
            print(f"  └─ Perceived Value: {trade['get_perceived']:6.1f}")
            print(f"  └─ Forecasted Value: {trade['get_forecasted']:6.1f}")
            print(f"  └─ Discount: {trade['get_discount']:6.1f}% (Undervalued)")
            print(f"\n💰 VALUE GAINED: +{trade['value_gain']:.1f} points ({trade['value_gain_pct']:.1f}%)")
            print(f"📊 MARKET PERCEPTION: Fair trade (similar perceived values)")
            print(f"✨ REALITY: You gain significant forecasted value!")
    
    @staticmethod
    def print_summary(stats: Dict):
        """Print summary statistics"""
        print("\n" + "="*80)
        print("📊 ANALYSIS SUMMARY")
        print("="*80)
        print(f"Total players analyzed: {stats['total_players']}")
        print(f"Undervalued players: {stats['undervalued_count']} ({stats['undervalued_count']/stats['total_players']*100:.1f}%)")
        print(f"Overvalued players: {stats['overvalued_count']} ({stats['overvalued_count']/stats['total_players']*100:.1f}%)")
        print(f"Fair value players: {stats['fair_value_count']} ({stats['fair_value_count']/stats['total_players']*100:.1f}%)")
        print(f"\nAverage discount/premium: {stats['avg_discount_premium']:.2f}%")
        print(f"Biggest discount: {stats['max_discount']:.2f}%")
        print(f"Biggest premium: {stats['max_premium']:.2f}%")