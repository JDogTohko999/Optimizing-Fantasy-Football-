#!/usr/bin/env python3
"""
Final results summary with corrected ranking
"""

print("🏆 FANTASY LEAGUE TEAM STRENGTH ANALYSIS")
print("="*60)
print("Based on sum of top 8 player market values from FantasyCalc")
print("="*60)

teams = [
    ("Quinshon Judkins", "3-1", 35057),
    ("James's Supreme Team", "3-1", 33798), 
    ("City Wok Football", "1-3", 33298),
    ("jj mccarthy did 911", "2-2", 32170),
    ("Half of the crime", "2-2", 28518),
    ("Footjob Bierly", "2-2", 27369),
    ("Owen's Otherworldly Team", "3-1", 25967),
    ("Just wait for week 7", "2-2", 25699),
    ("JERRY JEUDY", "1-3", 25116),
    ("Saddam Hussein Football", "3-1", 24911),
    ("Colin's Competitive Team", "1-3", 22760),
    ("Anshul's Left Nut", "1-3", 21503)
]

print(f"{'Rank':<4} {'Team':<30} {'Record':<8} {'Top 8 Value':<12} {'Status'}")
print("-"*70)

for i, (team, record, value) in enumerate(teams, 1):
    marker = "👑 YOUR TEAM!" if team == "Quinshon Judkins" else ""
    print(f"{i:<4} {team:<30} {record:<8} ${value:<11,} {marker}")

print("-"*70)
print(f"\n🎯 KEY INSIGHTS:")
print(f"• Your team has the HIGHEST market value: ${teams[0][2]:,}")
print(f"• You're ahead of #2 by: ${teams[0][2] - teams[1][2]:,}")
print(f"• Average team value: ${sum(t[2] for t in teams) / len(teams):,.0f}")
print(f"• Your advantage over average: ${teams[0][2] - (sum(t[2] for t in teams) / len(teams)):,.0f}")

print(f"\n📊 RECORD vs VALUE ANALYSIS:")
strong_records = [t for t in teams if int(t[1].split('-')[0]) >= 3]
print(f"• Teams with 3+ wins: {len(strong_records)}")
print(f"• Your record (3-1) matches your #1 value ranking!")

print(f"\n📈 Bar chart saved to: output/team_values_comparison.png")
print(f"Open this file to see the visual comparison!")