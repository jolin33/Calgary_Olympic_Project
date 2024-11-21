import csv
from collections import defaultdict

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Powerplay/Powerplanalysisfiltered.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Powerplay/Powerplanalysis.csv'

# Define goal probability constants
GOAL_PROBABILITIES = {
    'danger_zone': 0.18,    # 18% chance of scoring from danger zone on powerplay
    'non_danger': 0.09      # 9% chance of scoring from outside danger zone on powerplay
}

# Define weights
weights = {
    'Goal': 15,
    'Carried': 2,
    'Dumped': 2,
    'Faceoff Win': 3,
    'Danger Zone Shot': 5,
    'Carried Rate': 10,
    'Dumped Rate': 10,
    'Denial Rate': 10,
    'Entry Rate': 10,
    'Faceoff Win Rate': 10,
    'PP Success Rate': 15,
    'Expected Goals': 5,
    'Blocks': 2,
    'Takeaways': 2
}

def filter_data_by_date(file_path, filtered_path, start_date, end_date):
    """Filter the dataset by date range."""
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            game_date = row['game_date']
            if start_date <= game_date <= end_date:
                writer.writerow(row)

def initialize_team_stats():
    """Initialize dictionary for team statistics."""
    return {
        'total_score': 0,
        'total_goals': 0,
        'total_carried': 0,
        'total_dumped': 0,
        'total_zone_entries': 0,
        'faceoff_wins': 0,
        'total_faceoffs': 0,
        'danger_zone_shots': 0,
        'games_played': 0,
        'powerplay_count': 0,
        'successful_entries': 0,
        'entries': 0,
        'denials': 0,
        'shots': 0,
        'non_danger_shots': 0,
        'expected_goals': 0,
        'takeaways': 0,
        'blocked': 0,
        'total_entries': 0
    }

def get_shot_details(x_coord, y_coord):
    """Calculate shot zone and expected goals."""
    is_danger_zone = ((11 <= x_coord <= 19.8 or 180.2 <= x_coord <= 188.8) and 
                     (20.5 <= y_coord <= 64.4))
    
    if is_danger_zone:
        expected_goals = GOAL_PROBABILITIES['danger_zone']
    else:
        expected_goals = GOAL_PROBABILITIES['non_danger']
        
    return is_danger_zone, expected_goals

def calculate_powerplay_analysis(file_path):
    """Calculate powerplay analysis for all teams."""
    team_stats = defaultdict(initialize_team_stats)
    pp_opportunities = defaultdict(set)
    
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        current_game = None
        
        for row in reader:
            game_date = row['game_date']
            home_team = row['Home Team']
            away_team = row['Away Team']
            event = row['Event']
            detail = row['Detail 1']
            detail_2 = row['Detail 2']
            team = row['Team']
            player2 = row['Player 2']
            home_skaters = int(row['Home Team Skaters'])
            away_skaters = int(row['Away Team Skaters'])

            game_id = f"{game_date}_{home_team}_{away_team}"
            if game_id != current_game:
                current_game = game_id

            # Determine powerplay situation
            is_powerplay = False
            if team == home_team and home_skaters > away_skaters and away_skaters < 5:
                is_powerplay = True
                pp_opportunities[home_team].add(game_id)
            elif team == away_team and away_skaters > home_skaters and home_skaters < 5:
                is_powerplay = True
                pp_opportunities[away_team].add(game_id)

            if not is_powerplay:
                continue

            team_stats[team]['powerplay_count'] += 1
            team_stats[team]['games_played'] += 1

            # Process events
            if event == 'Goal':
                team_stats[team]['total_goals'] += 1
                team_stats[team]['total_score'] += weights['Goal']
                
            elif event == 'Zone Entry':
                team_stats[team]['entries'] += 1
                team_stats[team]['total_zone_entries'] += 1
                team_stats[team]['total_entries'] += 1

                if detail == 'Carried':
                    team_stats[team]['total_carried'] += 1
                    team_stats[team]['successful_entries'] += 1
                    team_stats[team]['total_score'] += weights['Carried']
                elif detail == 'Dumped':
                    team_stats[team]['total_dumped'] += 1
                    team_stats[team]['successful_entries'] += 1
                    team_stats[team]['total_score'] += weights['Dumped']
                    
            elif event == 'Faceoff Win':
                team_stats[team]['faceoff_wins'] += 1
                team_stats[team]['total_score'] += weights['Faceoff Win']
                team_stats[team]['total_faceoffs'] += 1
                if player2:
                    opposing_team = away_team if team == home_team else home_team
                    team_stats[opposing_team]['total_faceoffs'] += 1
            
            elif event == 'Takeaway':
                team_stats[team]['takeaways'] += 1
                team_stats[team]['total_score'] += weights['Takeaways']

            # Process blocked shots
            if event == 'Shot' and detail_2 == 'Blocked':
                blocking_team = away_team if team == home_team else home_team
                team_stats[blocking_team]['blocked'] += 1
                team_stats[blocking_team]['total_score'] += weights['Blocks']
            
            # Process shots and expected goals
            if event == 'Shot' and row['X Coordinate'] and row['Y Coordinate']:
                x_coord = float(row['X Coordinate'])
                y_coord = float(row['Y Coordinate'])
                team_stats[team]['shots'] += 1

                is_danger_zone, xg = get_shot_details(x_coord, y_coord)
                team_stats[team]['expected_goals'] += xg
                
                if is_danger_zone:
                    team_stats[team]['danger_zone_shots'] += 1
                    team_stats[team]['total_score'] += weights['Danger Zone Shot']
                else:
                    team_stats[team]['non_danger_shots'] += 1

            # Process denials
            if detail == 'Lost':
                team_stats[team]['denials'] += 1

    # Calculate final rates and scores
    for team, stats in team_stats.items():
        # Zone entry rates
        if stats['total_zone_entries'] > 0:
            stats['carried_rate'] = stats['total_carried'] / stats['total_zone_entries']
            stats['dumped_rate'] = stats['total_dumped'] / stats['total_zone_entries']
            stats['carried_rate_weight'] = stats['carried_rate'] * weights['Carried Rate']
            stats['dumped_rate_weight'] = stats['dumped_rate'] * weights['Dumped Rate']
            stats['total_score'] += stats['carried_rate_weight'] + stats['dumped_rate_weight']
        else:
            stats['carried_rate'] = stats['dumped_rate'] = 0
            stats['carried_rate_weight'] = stats['dumped_rate_weight'] = 0

        # Faceoff rates
        if stats['total_faceoffs'] > 0:
            stats['faceoff_win_rate'] = stats['faceoff_wins'] / stats['total_faceoffs']
            stats['total_score'] += stats['faceoff_win_rate'] * weights['Faceoff Win Rate']
        else:
            stats['faceoff_win_rate'] = 0

        # Powerplay success rate
        stats['pp_opportunities'] = len(pp_opportunities[team])
        if stats['pp_opportunities'] > 0:
            stats['pp_success_rate'] = stats['total_goals'] / stats['pp_opportunities']
            stats['total_score'] += stats['pp_success_rate'] * weights['PP Success Rate']
        else:
            stats['pp_success_rate'] = 0

        # Entry and denial rates
        if stats['total_entries'] > 0:
            stats['entry_rate'] = stats['successful_entries'] / stats['total_entries']
            stats['denial_rate'] = stats['denials'] / stats['entries'] if stats['entries'] > 0 else 0
            stats['total_score'] += (stats['entry_rate'] * weights['Entry Rate'] +
                                   stats['denial_rate'] * weights['Denial Rate'])
        else:
            stats['entry_rate'] = stats['denial_rate'] = 0

        # Expected goals calculations
        stats['expected_goals_weight'] = stats['expected_goals'] * weights['Expected Goals']
        stats['total_score'] += stats['expected_goals_weight']
        stats['goals_above_expected'] = stats['total_goals'] - stats['expected_goals']

    return sorted(team_stats.items(), key=lambda x: x[1]['total_score'], reverse=True)

def save_top_teams_to_csv(top_teams, output_file_path):
    """Save team analysis results to CSV."""
    fieldnames = [
        'Team', 'Total Score', 'Total Goals', 'PP Opportunities', 'PP Success Rate',
        'Expected Goals', 'Expected Goals Weight', 'Goals Above Expected',
        'Total Carried', 'Total Dumped', 'Total Zone Entries', 'Successful Entries',
        'Entry Rate', 'Denials', 'Denial Rate', 
        'Faceoff Wins', 'Total Faceoffs', 'Faceoff Win Rate',
        'Shots', 'Danger Zone Shots', 'Non-Danger Shots', 'Shot Danger Rate',
        'Takeaways', 'Blocked', 'Games Played', 'Powerplay Count',
        'Carried Rate', 'Dumped Rate', 'Carried Rate Weight', 'Dumped Rate Weight'
    ]
    
    with open(output_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(fieldnames)

        for team, stats in top_teams:
            shot_danger_rate = (stats['danger_zone_shots'] / stats['shots']) if stats['shots'] > 0 else 0
            writer.writerow([
                team,
                round(stats['total_score'], 2),
                stats['total_goals'],
                stats['pp_opportunities'],
                f"{stats['pp_success_rate']:.2f}",
                round(stats['expected_goals'], 2),
                round(stats['expected_goals_weight'], 2),
                round(stats['goals_above_expected'], 2),
                stats['total_carried'],
                stats['total_dumped'],
                stats['total_zone_entries'],
                stats['successful_entries'],
                f"{stats['entry_rate']:.2f}",
                stats['denials'],
                f"{stats['denial_rate']:.2f}",
                stats['faceoff_wins'],
                stats['total_faceoffs'],
                f"{stats['faceoff_win_rate']:.2f}",
                stats['shots'],
                stats['danger_zone_shots'],
                stats['non_danger_shots'],
                f"{shot_danger_rate:.2f}",
                stats['takeaways'],
                stats['blocked'],
                stats['games_played'],
                stats['powerplay_count'],
                f"{stats['carried_rate']:.2f}",
                f"{stats['dumped_rate']:.2f}",
                f"{stats['carried_rate_weight']:.2f}",
                f"{stats['dumped_rate_weight']:.2f}"
            ])
    print(f"Top powerplay teams saved to {output_file_path}")

if __name__ == "__main__":
    start_date = '2018-02-11'
    end_date = '2018-02-21'
    
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    best_teams_analysis = calculate_powerplay_analysis(filtered_file_path)
    save_top_teams_to_csv(best_teams_analysis, output_file_path)