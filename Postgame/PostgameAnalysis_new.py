import csv
from collections import defaultdict

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Postgame/filtered_postgame_dataset.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Postgame/postgame.csv'

# Define goal probability constants based on situation and location
GOAL_PROBABILITIES = {
    'powerplay': {
        'danger_zone': 0.18,    # 18% chance of scoring from danger zone on powerplay
        'non_danger': 0.09      # 9% chance of scoring from outside danger zone on powerplay
    },
    'even_strength': {
        'danger_zone': 0.15,    # 15% chance of scoring from danger zone at even strength
        'non_danger': 0.07      # 7% chance of scoring from outside danger zone at even strength
    },
    'shorthanded': {
        'danger_zone': 0.12,    # 12% chance of scoring from danger zone while shorthanded
        'non_danger': 0.05      # 5% chance of scoring from outside danger zone while shorthanded
    }
}

# Step 1: Filter the data by date
def filter_data_by_date(file_path, filtered_path, start_date, end_date):
    """Filter the CSV data by date range."""
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            game_date = row['game_date']
            if start_date <= game_date <= end_date:
                writer.writerow(row)

# Step 2: Calculate metrics for prescout analysis
def calculate_prescout_metrics(file_path):
    """Calculate metrics for prescout analysis."""
    team_stats = defaultdict(lambda: {
        'shorthanded': {'goals': 0, 'entries': 0, 'successful_entries': 0, 'denials': 0, 
                        'faceoff_wins': 0, 'shots': 0, 'shots_on_net': 0, 'danger_zone_shots': 0, 
                        'dumped': 0, 'carried': 0, 'takeaways': 0, 'blocked': 0, 'total_entries': 0,
                        'expected_goals': 0, 'non_danger_shots': 0},  # Added shots_on_net
        'powerplay': {'goals': 0, 'entries': 0, 'successful_entries': 0, 'denials': 0, 
                      'faceoff_wins': 0, 'shots': 0, 'shots_on_net': 0, 'danger_zone_shots': 0, 
                      'dumped': 0, 'carried': 0, 'takeaways': 0, 'blocked': 0, 'total_entries': 0,
                      'expected_goals': 0, 'non_danger_shots': 0},  # Added shots_on_net
        'even_strength': {'goals': 0, 'entries': 0, 'successful_entries': 0, 'denials': 0, 
                          'faceoff_wins': 0, 'shots': 0, 'shots_on_net': 0, 'danger_zone_shots': 0, 
                          'dumped': 0, 'carried': 0, 'takeaways': 0, 'blocked': 0, 'total_entries': 0,
                          'expected_goals': 0, 'non_danger_shots': 0}  # Added shots_on_net
    })

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            home_team = row['Home Team']
            away_team = row['Away Team']
            event_team = row['Team']
            event = row['Event']
            detail = row['Detail 1']
            detail_2 = row['Detail 2']  # For Blocked Shots and On Net
            home_skaters = int(row['Home Team Skaters'])
            away_skaters = int(row['Away Team Skaters'])
            
            # Determine category based on player counts with the condition for shorthanded
            if home_skaters > away_skaters and away_skaters <= 4:
                home_category = 'powerplay'
                away_category = 'shorthanded'
            elif away_skaters > home_skaters and home_skaters <= 4:
                home_category = 'shorthanded'
                away_category = 'powerplay'
            else:
                home_category = away_category = 'even_strength'
            
            category = home_category if event_team == home_team else away_category

            # Goals
            if event == 'Goal':
                team_stats[event_team][category]['goals'] += 1

            # Update logic for Dumped, Carried, Entries, and Successful Entries
            if event == 'Zone Entry':
                team_stats[event_team][category]['entries'] += 1
                team_stats[event_team][category]['total_entries'] += 1

                if detail == 'Dumped':
                    team_stats[event_team][category]['dumped'] += 1
                    team_stats[event_team][category]['successful_entries'] += 1
                elif detail == 'Carried':
                    team_stats[event_team][category]['carried'] += 1
                    team_stats[event_team][category]['successful_entries'] += 1

            # Update Denials based on event details
            if detail == 'Lost':
                team_stats[event_team][category]['denials'] += 1

            # Faceoff Wins
            if event == 'Faceoff Win':
                team_stats[event_team][category]['faceoff_wins'] += 1

            # Shots and Danger Zone Shots with Expected Goals
            if event == 'Shot' and row['X Coordinate'] and row['Y Coordinate']:
                x_coord = float(row['X Coordinate'])
                y_coord = float(row['Y Coordinate'])
                team_stats[event_team][category]['shots'] += 1
                
                # Add counter for shots on net
                if detail_2 == 'On Net':
                    team_stats[event_team][category]['shots_on_net'] += 1

                # Determine if shot is from danger zone and calculate expected goals
                is_danger_zone = (11 <= x_coord <= 19.8 or 180.2 <= x_coord <= 188.8) and (20.5 <= y_coord <= 64.4)
                
                if is_danger_zone:
                    team_stats[event_team][category]['danger_zone_shots'] += 1
                    team_stats[event_team][category]['expected_goals'] += GOAL_PROBABILITIES[category]['danger_zone']
                else:
                    team_stats[event_team][category]['non_danger_shots'] += 1
                    team_stats[event_team][category]['expected_goals'] += GOAL_PROBABILITIES[category]['non_danger']

            # Added logic for Takeaways
            elif event == 'Takeaway':
                team_stats[event_team][category]['takeaways'] += 1

            # Blocked Shots - if Shot event and Detail 2 is 'Blocked', increment the opponent's blocked shots
            if event == 'Shot' and detail_2 == 'Blocked':
                if event_team == home_team:
                    team_stats[away_team][category]['blocked'] += 1  # Opponent's blocked shot
                else:
                    team_stats[home_team][category]['blocked'] += 1  # Opponent's blocked shot

    return team_stats

def save_prescout_metrics_to_csv(team_stats, output_file):
    """Save prescout metrics to a CSV file."""
    with open(output_file, 'w', newline='') as file:
        headers = [
            'Team', 'Category', 'Goals', 'Expected Goals', 'Goals vs Expected', 
            'Entries', 'Successful Entries', 'Entry Rate', 
            'Denials', 'Denial Rate', 'Total Entries', 'Faceoff Wins', 'Faceoff Win Rate', 
            'Dump In Rate', 'Carried Rate', 'Dumped', 'Carried', 'Shots', 'Shots on Net',
            'Danger Zone Shots', 'Non-Danger Shots', 'Shot Danger Rate',
            'Takeaways', 'Blocked', 'Shooting Percentage'
        ]
        writer = csv.writer(file)
        writer.writerow(headers)

        # First, calculate total faceoff wins for each category
        total_faceoffs = defaultdict(int)
        for team_stats_value in team_stats.values():
            for category, stats in team_stats_value.items():
                total_faceoffs[category] += stats['faceoff_wins']

        for team, categories in team_stats.items():
            for category, stats in categories.items():
                entries = stats['entries']
                total_entries = stats['total_entries']
                successful_entries = stats['successful_entries']
                denials = stats['denials']
                faceoff_wins = stats['faceoff_wins']
                
                # Calculate metrics
                entry_rate = (successful_entries / total_entries) if total_entries > 0 else 0
                denial_rate = (denials / entries) if entries > 0 else 0
                faceoff_win_rate = (faceoff_wins / total_faceoffs[category]) if total_faceoffs[category] > 0 else 0
                dump_in_rate = stats['dumped'] / total_entries if total_entries > 0 else 0
                carried_rate = stats['carried'] / total_entries if total_entries > 0 else 0

                # Calculate new metrics for expected goals
                total_shots = stats['shots']
                danger_shots = stats['danger_zone_shots']
                shot_danger_rate = danger_shots / total_shots if total_shots > 0 else 0
                goals = stats['goals']
                shooting_percentage = (goals / total_shots * 100) if total_shots > 0 else 0
                goals_vs_expected = goals - stats['expected_goals']

                writer.writerow([
                    team, category.capitalize(), goals, f"{stats['expected_goals']:.2f}", 
                    f"{goals_vs_expected:.2f}", entries, successful_entries, 
                    f"{entry_rate:.2f}", denials, f"{denial_rate:.2f}", total_entries, 
                    faceoff_wins, f"{faceoff_win_rate:.2f}", f"{dump_in_rate:.2f}", 
                    f"{carried_rate:.2f}", stats['dumped'], stats['carried'], stats['shots'],
                    stats['shots_on_net'],  # Added shots on net to output
                    danger_shots, stats['non_danger_shots'], f"{shot_danger_rate:.2f}",
                    stats['takeaways'], stats['blocked'], f"{shooting_percentage:.2f}"
                ])

if __name__ == "__main__":
    start_date = '2019-02-17'
    end_date = '2019-02-17'
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    team_stats = calculate_prescout_metrics(filtered_file_path)
    save_prescout_metrics_to_csv(team_stats, output_file_path)