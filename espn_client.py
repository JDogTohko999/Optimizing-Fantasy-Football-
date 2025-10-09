"""
ESPN Fantasy Football API Client
Handles all interactions with ESPN's fantasy football API
"""
import requests
import pandas as pd
from typing import Dict, Optional, List
import fantasy_config as config

class ESPNClient:
    """Client for interacting with ESPN Fantasy Football API"""
    
    BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
    
    def __init__(self, league_id: int, season: int, espn_s2: str = None, swid: str = None):
        self.league_id = league_id
        self.season = season
        self.espn_s2 = espn_s2 or config.ESPN_S2
        self.swid = swid or config.SWID
        
        # Set up cookies if provided
        self.cookies = None
        if self.espn_s2 and self.swid:
            self.cookies = {
                'espn_s2': self.espn_s2,
                'SWID': self.swid
            }
    
    def _get_league_endpoint(self, view: List[str] = None) -> str:
        """Build the league endpoint URL"""
        return f"{self.BASE_URL}/seasons/{self.season}/segments/0/leagues/{self.league_id}"
    
    def _make_request(self, params: Dict = None) -> Optional[Dict]:
        """Make a request to the ESPN API"""
        url = self._get_league_endpoint()
        
        try:
            response = requests.get(url, params=params, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to ESPN API: {e}")
            if response.status_code == 401:
                print("Authentication failed. Check your ESPN_S2 and SWID cookies.")
            return None
    
    def get_league_info(self) -> Optional[Dict]:
        """Get basic league information"""
        params = {'view': 'mSettings'}
        data = self._make_request(params)
        
        if data:
            settings = data.get('settings', {})
            return {
                'name': settings.get('name', 'Unknown League'),
                'size': settings.get('size', 0),
                'scoring_format': 'PPR' if settings.get('scoringSettings', {}).get('scoringItems', {}) else 'Unknown'
            }
        return None
    
    def get_all_teams(self) -> pd.DataFrame:
        """Get all teams in the league"""
        params = {'view': 'mTeam'}
        data = self._make_request(params)
        
        if not data:
            return pd.DataFrame()
        
        teams = []
        for team in data.get('teams', []):
            # Try different name field patterns
            team_name = team.get('name', '')
            if not team_name:
                # Fallback to location + nickname if name is empty
                location = team.get('location', '')
                nickname = team.get('nickname', '')
                team_name = f"{location} {nickname}".strip()
            
            teams.append({
                'team_id': team.get('id'),
                'team_name': team_name,
                'owner': team.get('primaryOwner', 'Unknown'),
                'wins': team.get('record', {}).get('overall', {}).get('wins', 0),
                'losses': team.get('record', {}).get('overall', {}).get('losses', 0),
                'points_for': team.get('record', {}).get('overall', {}).get('pointsFor', 0)
            })
        
        return pd.DataFrame(teams)
    
    def get_all_rosters(self) -> pd.DataFrame:
        """Get all rosters in the league"""
        params = {'view': ['mRoster', 'mTeam']}
        data = self._make_request(params)
        
        if not data:
            return pd.DataFrame()
        
        rosters = []
        teams = data.get('teams', [])
        
        # Position mapping (ESPN position IDs)
        position_map = {
            0: 'QB',
            1: 'TQB',  # Team QB (not used in most leagues)
            2: 'RB',
            3: 'RB/WR',  # Flex
            4: 'WR',
            5: 'WR/TE',  # Flex
            6: 'TE',
            7: 'OP',  # Offensive Player
            16: 'D/ST',
            17: 'K',
            20: 'FLEX',
            21: 'FLEX',
            23: 'FLEX'
        }
        
        for team in teams:
            # Try different name field patterns (same as get_all_teams method)
            team_name = team.get('name', '')
            if not team_name:
                # Fallback to location + nickname if name is empty
                location = team.get('location', '')
                nickname = team.get('nickname', '')
                team_name = f"{location} {nickname}".strip()
            
            team_id = team.get('id')
            
            roster = team.get('roster', {})
            entries = roster.get('entries', [])
            
            for entry in entries:
                player_pool_entry = entry.get('playerPoolEntry', {})
                player = player_pool_entry.get('player', {})
                
                player_id = player.get('id')
                player_name = player.get('fullName', 'Unknown')
                
                # Get primary position
                default_pos_id = player.get('defaultPositionId', 0)
                position = position_map.get(default_pos_id, 'FLEX')
                
                # Get eligible positions
                eligible_slots = player.get('eligibleSlots', [])
                eligible_positions = [position_map.get(slot, '') for slot in eligible_slots]
                eligible_positions = [pos for pos in eligible_positions if pos]
                
                rosters.append({
                    'player_id': player_id,
                    'player_name': player_name,
                    'position': position,
                    'eligible_positions': ', '.join(eligible_positions),
                    'team_name': team_name,
                    'team_id': team_id,
                    'pro_team': player.get('proTeamId', 0)
                })
        
        return pd.DataFrame(rosters)
    
    def get_current_week(self) -> int:
        """Get the current scoring period (week)"""
        params = {'view': 'mSettings'}
        data = self._make_request(params)
        
        if data:
            status = data.get('status', {})
            return status.get('currentMatchupPeriod', 1)
        return 1
    
    def get_rest_of_season_projections(self) -> pd.DataFrame:
        """
        Get rest of season projections from ESPN
        This is REDRAFT-specific - focuses on remaining games only
        """
        params = {'view': 'kona_player_info'}
        data = self._make_request(params)
        
        if not data:
            return pd.DataFrame()
        
        current_week = self.get_current_week()
        weeks_remaining = 18 - current_week  # Standard 18-week season
        
        projections = []
        players = data.get('players', [])
        
        for player_data in players:
            player = player_data.get('player', {})
            player_id = player.get('id')
            player_name = player.get('fullName')
            
            if not player_name:
                continue
            
            # Get stats - looking for rest of season projections
            stats = player.get('stats', [])
            
            # Try to get remaining season projection
            total_projection = 0
            games_played = 0
            season_total = 0
            
            for stat in stats:
                stat_source_id = stat.get('statSourceId', 0)
                stat_split_type_id = stat.get('statSplitTypeId', 0)
                
                # statSourceId 1 = projection, 0 = actual
                # Look for season total projection (statSplitTypeId 0)
                if stat_source_id == 1 and stat_split_type_id == 0:
                    total_projection = stat.get('appliedTotal', 0)
                
                # Get actual stats to calculate remaining
                if stat_source_id == 0 and stat_split_type_id == 0:
                    season_total = stat.get('appliedTotal', 0)
            
            # Calculate rest of season projection
            # If we have season projection, use it; otherwise estimate
            if total_projection > 0:
                # Assume linear projection through remaining weeks
                avg_per_week = total_projection / 18
                remaining_projection = avg_per_week * weeks_remaining
            else:
                # Use current pace if no projection available
                if current_week > 0:
                    avg_per_week = season_total / current_week
                    remaining_projection = avg_per_week * weeks_remaining
                else:
                    remaining_projection = 0
            
            projections.append({
                'player_id': player_id,
                'player_name': player_name,
                'season_projection': total_projection,
                'season_actual': season_total,
                'rest_of_season_projection': remaining_projection,
                'avg_per_week': remaining_projection / weeks_remaining if weeks_remaining > 0 else 0
            })
        
        df = pd.DataFrame(projections)
        # Filter out players with no projection
        df = df[df['rest_of_season_projection'] > 0]
        
        return df
    
    def get_player_stats_last_4_weeks(self) -> pd.DataFrame:
        """
        Get recent performance (last 4 weeks) - important for redraft
        Recent performance matters more in redraft than dynasty
        """
        current_week = self.get_current_week()
        recent_weeks = max(1, current_week - 4)
        
        params = {'view': 'kona_player_info'}
        data = self._make_request(params)
        
        if not data:
            return pd.DataFrame()
        
        recent_stats = []
        players = data.get('players', [])
        
        for player_data in players:
            player = player_data.get('player', {})
            player_name = player.get('fullName')
            
            if not player_name:
                continue
            
            stats = player.get('stats', [])
            
            # Sum up last 4 weeks of actual performance
            recent_points = 0
            weeks_counted = 0
            
            for stat in stats:
                stat_source_id = stat.get('statSourceId', 0)  # 0 = actual
                scoring_period_id = stat.get('scoringPeriodId', 0)
                
                if stat_source_id == 0 and scoring_period_id >= recent_weeks and scoring_period_id < current_week:
                    recent_points += stat.get('appliedTotal', 0)
                    weeks_counted += 1
            
            if weeks_counted > 0:
                recent_stats.append({
                    'player_name': player_name,
                    'recent_total': recent_points,
                    'recent_avg': recent_points / weeks_counted,
                    'weeks_played': weeks_counted
                })
        
        return pd.DataFrame(recent_stats)

    def get_weekly_matchups(self, week: int = None) -> pd.DataFrame:
        """Get matchups for a specific week (useful for playoff planning)"""
        if week is None:
            week = self.get_current_week()
        
        params = {
            'view': 'mMatchup',
            'scoringPeriodId': week
        }
        data = self._make_request(params)
        
        if not data:
            return pd.DataFrame()
        
        matchups = []
        schedule = data.get('schedule', [])
        
        for game in schedule:
            if game.get('matchupPeriodId') == week:
                home_team = game.get('home', {})
                away_team = game.get('away', {})
                
                matchups.append({
                    'week': week,
                    'home_team_id': home_team.get('teamId'),
                    'away_team_id': away_team.get('teamId'),
                    'home_score': home_team.get('totalPoints', 0),
                    'away_score': away_team.get('totalPoints', 0)
                })
        
        return pd.DataFrame(matchups)