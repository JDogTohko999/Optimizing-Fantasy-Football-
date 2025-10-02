"""
Setup Helper Script
Helps you configure your .env file and test ESPN connection
"""
import os
import sys
from pathlib import Path

def create_env_file():
    """Interactive setup for .env file"""
    print("\n" + "="*80)
    print("ESPN FANTASY FOOTBALL TRADE OPTIMIZER - SETUP")
    print("="*80)
    
    if Path('.env').exists():
        response = input("\n.env file already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📋 Let's set up your configuration...")
    print("\nYou can find your League ID in your ESPN league URL:")
    print("Example: https://fantasy.espn.com/football/league?leagueId=123456")
    print("         Your League ID is: 123456")
    
    # Get league info
    league_id = input("\nEnter your League ID: ").strip()
    season = input("Enter season year (default: 2025): ").strip() or "2025"
    
    print("\n" + "="*80)
    print("AUTHENTICATION SETUP")
    print("="*80)
    print("\nFor PRIVATE leagues, you need ESPN cookies.")
    print("For PUBLIC leagues, you can skip this (just press Enter).")
    print("\nHow to get your cookies:")
    print("1. Log into ESPN Fantasy Football in your browser")
    print("2. Press F12 to open Developer Tools")
    print("3. Go to Application tab (Chrome) or Storage tab (Firefox)")
    print("4. Click 'Cookies' → 'https://fantasy.espn.com'")
    print("5. Find 'espn_s2' and 'SWID' and copy their values")
    
    espn_s2 = input("\nEnter your espn_s2 cookie (or press Enter to skip): ").strip()
    swid = input("Enter your SWID cookie (or press Enter to skip): ").strip()
    
    # Get league settings
    print("\n" + "="*80)
    print("LEAGUE SETTINGS")
    print("="*80)
    
    scoring_format = input("Scoring format (ppr/half_ppr/standard, default: ppr): ").strip().lower() or "ppr"
    num_teams = input("Number of teams (default: 12): ").strip() or "12"
    num_qbs = input("Number of starting QBs (1 or 2 for superflex, default: 1): ").strip() or "1"
    
    # Create .env file
    env_content = f"""# ESPN League Configuration
LEAGUE_ID={league_id}
SEASON={season}

# ESPN Authentication (Required for private leagues)
ESPN_S2={espn_s2}
SWID={swid}

# Optional: Your team name (leave blank to select interactively)
YOUR_TEAM_NAME=

# League Settings
SCORING_FORMAT={scoring_format}
NUM_TEAMS={num_teams}
NUM_QBS={num_qbs}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("\n✅ .env file created successfully!")
    print("\nYou can now run: python main.py")
    
    # Test connection
    test = input("\nWould you like to test your ESPN connection? (y/n): ")
    if test.lower() == 'y':
        test_espn_connection(league_id, season, espn_s2, swid)

def test_espn_connection(league_id: str, season: str, espn_s2: str, swid: str):
    """Test connection to ESPN API"""
    print("\n" + "="*80)
    print("TESTING ESPN CONNECTION")
    print("="*80)
    
    try:
        import requests
        
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
        
        cookies = None
        if espn_s2 and swid:
            cookies = {'espn_s2': espn_s2, 'SWID': swid}
        
        params = {'view': 'mSettings'}
        
        print("\nAttempting to connect...")
        response = requests.get(url, params=params, cookies=cookies, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            league_name = data.get('settings', {}).get('name', 'Unknown')
            league_size = data.get('settings', {}).get('size', 0)
            
            print("\n✅ CONNECTION SUCCESSFUL!")
            print(f"\nLeague: {league_name}")
            print(f"Teams: {league_size}")
            print("\nYou're all set! Run 'python main.py' to start analyzing trades.")
        
        elif response.status_code == 401:
            print("\n❌ AUTHENTICATION FAILED")
            print("\nYour cookies are incorrect or expired.")
            print("Please double-check your espn_s2 and SWID values.")
            print("\nTips:")
            print("- Make sure SWID includes the curly braces: {XXXX-XXXX-...}")
            print("- espn_s2 is usually 100+ characters long")
            print("- Cookies expire periodically - you may need to refresh them")
        
        else:
            print(f"\n❌ CONNECTION FAILED (Status {response.status_code})")
            print(f"\nResponse: {response.text[:200]}")
    
    except ImportError:
        print("\n⚠ Please install requirements first:")
        print("pip install -r requirements.txt")
    
    except Exception as e:
        print(f"\n❌ Error testing connection: {e}")

def show_help():
    """Show help information"""
    print("\n" + "="*80)
    print("ESPN FANTASY FOOTBALL TRADE OPTIMIZER - HELP")
    print("="*80)
    
    print("\n📚 QUICK START:")
    print("1. Run: python setup_helper.py")
    print("2. Follow the prompts to configure")
    print("3. Run: python main.py")
    
    print("\n🔑 GETTING ESPN COOKIES:")
    print("For private leagues, you need espn_s2 and SWID cookies.")
    
    print("\nChrome:")
    print("1. Open ESPN Fantasy and log in")
    print("2. Press F12 → Application tab")
    print("3. Cookies → https://fantasy.espn.com")
    print("4. Copy espn_s2 and SWID values")
    
    print("\nFirefox:")
    print("1. Open ESPN Fantasy and log in")
    print("2. Press F12 → Storage tab")
    print("3. Cookies → https://fantasy.espn.com")
    print("4. Copy espn_s2 and SWID values")
    
    print("\n⚙️ CONFIGURATION:")
    print("Edit .env file or re-run setup:")
    print("- LEAGUE_ID: Found in your league URL")
    print("- SEASON: Current year (2025)")
    print("- ESPN_S2 & SWID: Your authentication cookies")
    print("- SCORING_FORMAT: ppr, half_ppr, or standard")
    
    print("\n🔧 ADVANCED SETTINGS:")
    print("Edit config.py to adjust:")
    print("- MIN_DISCOUNT_THRESHOLD: Minimum % to flag undervalued")
    print("- VALUE_MATCH_TOLERANCE: How close trades need to be")
    print("- POSITION_SCARCITY_MULTIPLIERS: Position value adjustments")
    
    print("\n📁 OUTPUT:")
    print("Results saved to output/ directory:")
    print("- trade_analysis_*.csv: Full player analysis")
    print("- trade_suggestions_*.csv: Recommended trades")
    
    print("\n❓ TROUBLESHOOTING:")
    print("- 'Authentication failed': Update your cookies")
    print("- 'No players with complete data': Check player name matching")
    print("- 'Rate limited': Wait a few minutes and retry")
    
    print("\n📖 For more info, see README.md")
    print("\n")

def main():
    """Main setup function"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            return
    
    print("\nESPN Fantasy Football Trade Optimizer - Setup Helper")
    print("\nWhat would you like to do?")
    print("1. Create/update .env configuration")
    print("2. Test ESPN connection")
    print("3. Show help")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        create_env_file()
    elif choice == '2':
        if not Path('.env').exists():
            print("\n⚠ No .env file found. Please run setup first (option 1)")
            return
        
        from dotenv import load_dotenv
        load_dotenv()
        
        league_id = os.getenv('LEAGUE_ID', '131646632')
        season = os.getenv('SEASON', '2025')
        espn_s2 = os.getenv('ESPN_S2', 'AEC6nVk57%2BKW64BRrVWqhlYHwKPkmoqB7X0E%2Bdv6FYv7YDizE0AA0UeYVFLkL6pMkexvl0gAuSgQq5vJopXbcJIB5O79NTSMx0fzlTTl7wEiSo8QpE0ryPjDk1EN56Gt%2Be7GwY0loQHQIpomPid56Sn7EY9xhVF%2FVESDBWEICXiTc11yq%2FhBivuy%2BPeOBuQcCv9KijniOUUPvl1RoHVlfiLyxZFkgUWShgCOgJ5y4KNmjVX4VrWM%2F%2F4W9EsbGk4c%2F3J5KIqIyfHkLFgkljGx3F2V')
        swid = os.getenv('SWID', '{04B39628-3578-4561-B753-B8A14E4F5DF2}')
        
        test_espn_connection(league_id, season, espn_s2, swid)
    elif choice == '3':
        show_help()
    elif choice == '4':
        print("\nExiting...")
    else:
        print("\nInvalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)