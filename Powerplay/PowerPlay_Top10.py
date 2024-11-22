import csv
from collections import defaultdict
import math

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Powerplay/Powerplaytop10filtered.csv'
output_file_path = '//Users/joshuaolin/Desktop/Calgary/NewDraft/Powerplay/Powerplaytop10analysis.csv'

# Define goal probability constants
GOAL_PROBABILITIES = {
    'danger_zone': 0.18,    # 18% chance of scoring from danger zone on powerplay
    'non_danger': 0.09      # 9% chance of scoring from outside danger zone on powerplay
}

# Define weights for scoring
weights = {
    'Goal': 10,               
    'Penalty Taken': -3,     
    'Puck Recovery': 2,      
    'Faceoff Win': 4,        
    'Carried': 2,            
    'Dumped': 1,            
    'Shot': 1,              
    'Danger Zone Shot': 2,   
    'Carried Rate': 10,
    'Dumped Rate': 10,
    'Denial Rate': 10,
    'Entry Rate': 10,
    'Faceoff Win Rate': 10,
    'Expected Goals': 5
}

def filter_data_by_date(file_path, filtered_path, start_date, end_date):
    """Filter the dataset by a specified date range and save to a new CSV."""
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            game_date = row['game_date']
            if start_date <= game_date <= end_date:
                writer.writerow(row)

def is_powerplay(row, event_team):
    """Determine if the team is on powerplay."""
    home_team = row['Home Team']
    home_skaters = int(row['Home Team Skaters'])
    away_skaters = int(row['Away Team Skaters'])
    
    if event_team == home_team:
        return home_skaters > away_skaters and away_skaters <= 4
    else:
        return away_skaters > home_skaters and home_skaters <= 4

def get_shot_details(x_coord, y_coord):
    """Calculate if shot is from danger zone and determine expected goal value."""
    if x_coord > 100:
        x_coord = 200 - x_coord
        y_coord = 85 - y_coord
    
    is_danger_zone = ((11 <= x_coord <= 19.8 or 180.2 <= x_coord <= 188.8) and 
                    (20.5 <= y_coord <= 64.4))
    
    if is_danger_zone:
        expected_goals = GOAL_PROBABILITIES['danger_zone']
    else:
        expected_goals = GOAL_PROBABILITIES['non_danger']
        
    return is_danger_zone, expected_goals

def initialize_player_stats(team, opponent):
    """Initialize dictionary for player statistics."""
    return {
        'team': team,
        'total_score': 0,
        'goals': 0,
        'penalties': 0,
        'faceoff_wins': 0,
        'total_faceoffs': 0,
        'carried': 0,
        'dumped': 0,
        'total_entries': 0,
        'successful_entries': 0,
        'denials': 0,
        'shots': 0,
        'danger_zone_shots': 0,
        'total_shots': 0,
        'non_danger_shots': 0,
        'expected_goals': 0,
        'powerplay_time': 0
    }

def calculate_powerplay_player_scores(file_path):
    """Calculate player scores during powerplay situations."""
    player_stats = {}

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            event_team = row['Team']
            event = row['Event']
            detail = row['Detail 1']
            detail_2 = row['Detail 2']
            player = row['Player']
            player2 = row['Player 2']

            # Only process powerplay situations
            if not is_powerplay(row, event_team):
                continue

            # Initialize players if needed
            for p in [player, player2]:
                if p and p not in player_stats:
                    opponent = row['Away Team'] if event_team == row['Home Team'] else row['Home Team']
                    player_stats[p] = initialize_player_stats(
                        event_team if p == player else opponent,
                        opponent if p == player else event_team
                    )

            if player:
                # Process shots
                if event == 'Shot':
                    player_stats[player]['total_shots'] += 1
                    if detail_2 != 'Blocked':
                        player_stats[player]['shots'] += 1
                        player_stats[player]['total_score'] += weights['Shot']
                        
                        try:
                            x_coord = float(row['X Coordinate'])
                            y_coord = float(row['Y Coordinate'])
                            is_danger_zone, expected_goals = get_shot_details(x_coord, y_coord)
                            
                            if is_danger_zone:
                                player_stats[player]['danger_zone_shots'] += 1
                                player_stats[player]['total_score'] += weights['Danger Zone Shot']
                            else:
                                player_stats[player]['non_danger_shots'] += 1
                            
                            player_stats[player]['expected_goals'] += expected_goals
                            
                        except (ValueError, TypeError):
                            pass

                # Process other events
                if event == 'Goal':
                    player_stats[player]['goals'] += 1
                    player_stats[player]['total_score'] += weights['Goal']
                elif event == 'Penalty Taken':
                    player_stats[player]['penalties'] += 1
                    player_stats[player]['total_score'] += weights['Penalty Taken']
                elif event == 'Puck Recovery':
                    player_stats[player]['total_score'] += weights['Puck Recovery']
                elif event == 'Faceoff Win':
                    player_stats[player]['faceoff_wins'] += 1
                    player_stats[player]['total_score'] += weights['Faceoff Win']
                    player_stats[player]['total_faceoffs'] += 1
                    if player2:
                        player_stats[player2]['total_faceoffs'] += 1

                elif event == 'Zone Entry':
                    player_stats[player]['total_entries'] += 1
                    if detail in ['Carried', 'Dumped']:
                        player_stats[player][detail.lower()] += 1
                        player_stats[player]['total_score'] += weights[detail]
                        player_stats[player]['successful_entries'] += 1

                # Process denials
                if (event == 'Dump In/Out' and detail == 'Lost' and player2) or \
                   (event in ['Incomplete Play', 'Takeaway'] and 
                    row['X Coordinate'] and 29 <= float(row['X Coordinate']) <= 207):
                    player_stats[player]['denials'] += 1

        # Calculate final rates and scores
        for stats in player_stats.values():
            if stats['total_entries'] > 0:
                stats['entry_rate'] = stats['successful_entries'] / stats['total_entries']
                stats['denial_rate'] = stats['denials'] / stats['total_entries']
                stats['carried_rate'] = stats['carried'] / stats['total_entries']
                stats['dumped_rate'] = stats['dumped'] / stats['total_entries']
                
                # Add rate weights to total score
                stats['total_score'] += (
                    stats['entry_rate'] * weights['Entry Rate'] +
                    stats['denial_rate'] * weights['Denial Rate'] +
                    stats['carried_rate'] * weights['Carried Rate'] +
                    stats['dumped_rate'] * weights['Dumped Rate']
                )
            else:
                stats['entry_rate'] = stats['denial_rate'] = 0
                stats['carried_rate'] = stats['dumped_rate'] = 0

            if stats['total_faceoffs'] > 0:
                stats['faceoff_win_rate'] = stats['faceoff_wins'] / stats['total_faceoffs']
                stats['total_score'] += stats['faceoff_win_rate'] * weights['Faceoff Win Rate']
            else:
                stats['faceoff_win_rate'] = 0

            # Add expected goals to total score
            stats['total_score'] += stats['expected_goals'] * weights['Expected Goals']
            stats['goals_above_expected'] = stats['goals'] - stats['expected_goals']

    return player_stats

def save_powerplay_players_to_csv(player_stats, output_file_path):
    """Save powerplay player statistics to CSV file."""
    fieldnames = [
        'Player', 'Team', 'Total Score', 'Goals', 'Expected Goals', 'Goals Above Expected',
        'Penalties', 'Faceoff Wins', 'Faceoff Win Rate',
        'Carried', 'Dumped', 'Total Entries', 'Successful Entries',
        'Denials', 'Entry Rate', 'Denial Rate',
        'Shots', 'Danger Zone Shots', 'Non-Danger Shots', 'Shot Accuracy',
        'Carried Rate', 'Dumped Rate'
    ]
    
    with open(output_file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['total_score'], reverse=True)
        for player, stats in sorted_players:
            writer.writerow({
                'Player': player,
                'Team': stats['team'],
                'Total Score': round(stats['total_score'], 2),
                'Goals': stats['goals'],
                'Expected Goals': round(stats['expected_goals'], 2),
                'Goals Above Expected': round(stats['goals_above_expected'], 2),
                'Penalties': stats['penalties'],
                'Faceoff Wins': stats['faceoff_wins'],
                'Faceoff Win Rate': round(stats['faceoff_win_rate'] * 100, 1),
                'Carried': stats['carried'],
                'Dumped': stats['dumped'],
                'Total Entries': stats['total_entries'],
                'Successful Entries': stats['successful_entries'],
                'Denials': stats['denials'],
                'Entry Rate': round(stats['entry_rate'] * 100, 1),
                'Denial Rate': round(stats['denial_rate'] * 100, 1),
                'Shots': stats['shots'],
                'Danger Zone Shots': stats['danger_zone_shots'],
                'Non-Danger Shots': stats['non_danger_shots'],
                'Shot Accuracy': round((stats['shots'] / stats['total_shots'] * 100 if stats['total_shots'] > 0 else 0), 1),
                'Carried Rate': round(stats['carried_rate'] * 100, 1),
                'Dumped Rate': round(stats['dumped_rate'] * 100, 1)
            })
    print(f"Powerplay player stats saved to {output_file_path}")

if __name__ == "__main__":
    # Use the same date range as PrescoutAnalysis
    start_date = '2018-02-11'
    end_date = '2018-02-21'
    
    # Filter data for the date range
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    
    # Calculate and save player value scores
    player_stats = calculate_powerplay_player_scores(filtered_file_path)
    save_powerplay_players_to_csv(player_stats, output_file_path)