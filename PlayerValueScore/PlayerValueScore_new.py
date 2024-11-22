import csv
from collections import defaultdict
import math

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/PlayerValueScore/filtered_playervaluescore_dataset.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/PlayerValueScore/playervalue_analysis.csv'

# Define weights for scoring
weights = {
    'Goal': {
        'evenstrength': 4,
        'powerplay': 3,
        'shorthanded': 6
    },
    'Expected_Value': {
        'evenstrength': 2,
        'powerplay': 1.5,
        'shorthanded': 3
    },
    'Penalty Taken': {
        'evenstrength': -2,
        'powerplay': -3,
        'shorthanded': -2
    },
    'Puck Recovery': {
        'evenstrength': 2,
        'powerplay': 2,
        'shorthanded': 3
    },
    'Faceoff Win': {
        'evenstrength': 3,
        'powerplay': 4,
        'shorthanded': 4
    },
    'Carried': {
        'evenstrength': 2,
        'powerplay': 2,
        'shorthanded': 3
    },
    'Dumped': {
        'evenstrength': 2,
        'powerplay': 1,
        'shorthanded': 3
    },
    'Shot': {
        'evenstrength': 1,
        'powerplay': 1,
        'shorthanded': 2
    },
    'Shot on Net': {  # Added new weight category for shots on net
        'evenstrength': 2,
        'powerplay': 2,
        'shorthanded': 3
    },
    'Danger Zone Shot': {
        'evenstrength': 2,
        'powerplay': 2,
        'shorthanded': 3
    },
    'Carried Rate': 10,
    'Dumped Rate': 10,
    'Denial Rate': 10,
    'Entry Rate': 10,
    'Faceoff Win Rate': 10
}

# Step 1: Filter data by date range
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

def determine_game_situation(row, event_team):
    """Determine if the team is on powerplay, shorthanded, or even strength."""
    home_team = row['Home Team']
    home_skaters = int(row['Home Team Skaters'])
    away_skaters = int(row['Away Team Skaters'])
    
    if event_team == home_team:
        if home_skaters > away_skaters and away_skaters <= 4:
            return 'powerplay'
        elif home_skaters < away_skaters and home_skaters <= 4:
            return 'shorthanded'
    else:
        if away_skaters > home_skaters and home_skaters <= 4:
            return 'powerplay'
        elif away_skaters < home_skaters and away_skaters <= 4:
            return 'shorthanded'
    return 'evenstrength'

# Step 2: Calculate player value scores
def calculate_player_value_scores(file_path):
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

            situation = determine_game_situation(row, event_team)

            # Get coordinates
            try:
                x_coord = float(row['X Coordinate'])
            except ValueError:
                x_coord = None

            # Initialize player in dictionary if not present
            for p in [player, player2]:
                if p and p not in player_stats:
                    player_stats[p] = {
                        'total_score': 0,
                        'expected_value': 0,
                        'goals': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'expected_goals': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'penalties': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'faceoff_wins': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'carried': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'dumped': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'shots': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'shots_on_net': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},  # Added shots on net
                        'danger_zone_shots': {'evenstrength': 0, 'powerplay': 0, 'shorthanded': 0, 'total': 0},
                        'total_shots': 0,
                        'total_entries': 0,
                        'successful_entries': 0,
                        'denials': 0,
                        'total_faceoffs': 0
                    }

            if player:
                stats = player_stats[player]
                
                # Process shots and expected goals
                if event == 'Shot':
                    stats['total_shots'] += 1
                    if detail_2 != 'Blocked':
                        stats['shots'][situation] += 1
                        stats['shots']['total'] += 1
                        stats['total_score'] += weights['Shot'][situation]
                        
                        # Add counter for shots on net
                        if detail_2 == 'On Net':
                            stats['shots_on_net'][situation] += 1
                            stats['shots_on_net']['total'] += 1
                            stats['total_score'] += weights['Shot on Net'][situation]
                        
                        try:
                            x_coord = float(row['X Coordinate'])
                            y_coord = float(row['Y Coordinate'])
                            
                            # Standardize coordinates
                            if x_coord > 100:
                                x_coord = 200 - x_coord
                                y_coord = 85 - y_coord
                            
                            distance = math.sqrt((x_coord - 0)**2 + (y_coord - 42.5)**2)
                            angle = abs(math.atan2(y_coord - 42.5, x_coord))
                            
                            # Calculate expected goals
                            xg = 0.09
                            xg *= 0.985 ** (distance/10)
                            xg *= 0.985 ** (math.degrees(angle))
                            
                            # Check for danger zone
                            if ((11 <= x_coord <= 19.8 or 180.2 <= x_coord <= 188.8) and 
                                (20.5 <= y_coord <= 64.4)):
                                stats['danger_zone_shots'][situation] += 1
                                stats['danger_zone_shots']['total'] += 1
                                xg *= 2.0
                                stats['total_score'] += weights['Danger Zone Shot'][situation]
                            
                            # Apply situation weights to expected goals
                            weighted_xg = xg * weights['Expected_Value'][situation]
                            stats['expected_goals'][situation] += weighted_xg
                            stats['expected_goals']['total'] += weighted_xg
                            
                        except (ValueError, TypeError):
                            pass

                # Process other events
                if event == 'Goal':
                    stats['goals'][situation] += 1
                    stats['goals']['total'] += 1
                    stats['total_score'] += weights['Goal'][situation]
                
                elif event == 'Penalty Taken':
                    stats['penalties'][situation] += 1
                    stats['penalties']['total'] += 1
                    stats['total_score'] += weights['Penalty Taken'][situation]
                
                elif event == 'Puck Recovery':
                    stats['total_score'] += weights['Puck Recovery'][situation]
                
                elif event == 'Faceoff Win':
                    stats['faceoff_wins'][situation] += 1
                    stats['faceoff_wins']['total'] += 1
                    stats['total_score'] += weights['Faceoff Win'][situation]
                    stats['total_faceoffs'] += 1
                    if player2:
                        player_stats[player2]['total_faceoffs'] += 1

                elif event == 'Zone Entry':
                    stats['total_entries'] += 1
                    if detail == 'Carried':
                        stats['carried'][situation] += 1
                        stats['carried']['total'] += 1
                        stats['total_score'] += weights['Carried'][situation]
                        stats['successful_entries'] += 1
                    elif detail == 'Dumped':
                        stats['dumped'][situation] += 1
                        stats['dumped']['total'] += 1
                        stats['total_score'] += weights['Dumped'][situation]
                        stats['successful_entries'] += 1

                # Calculate denials using Entry Defense Analysis (a) logic
                if event == 'Dump In/Out' and detail == 'Lost':
                    if player and player2:
                        player_stats[player2]['denials'] += 1
                elif event == 'Incomplete Play' and x_coord is not None:
                    if 29 <= x_coord <= 207 and player and player2:
                        player_stats[player2]['denials'] += 1
                elif event == 'Takeaway' and x_coord is not None:
                    if 29 <= x_coord <= 207 and player:
                        player_stats[player]['denials'] += 1

        # Calculate rates and expected value
        for stats in player_stats.values():
            # Entry rates
            if stats['total_entries'] > 0:
                stats['entry_rate'] = stats['successful_entries'] / stats['total_entries']
                stats['denial_rate'] = stats['denials'] / stats['total_entries']
                stats['carried_rate'] = stats['carried']['total'] / stats['total_entries']
                stats['dumped_rate'] = stats['dumped']['total'] / stats['total_entries']
                
                # Add rate weights to total score
                stats['total_score'] += (
                    stats['entry_rate'] * weights['Entry Rate'] +
                    stats['denial_rate'] * weights['Denial Rate'] +
                    stats['carried_rate'] * weights['Carried Rate'] +
                    stats['dumped_rate'] * weights['Dumped Rate']
                )
            else:
                stats['entry_rate'] = stats['denial_rate'] = stats['carried_rate'] = stats['dumped_rate'] = 0

            # Faceoff rate
            if stats['total_faceoffs'] > 0:
                stats['faceoff_win_rate'] = stats['faceoff_wins']['total'] / stats['total_faceoffs']
                stats['total_score'] += stats['faceoff_win_rate'] * weights['Faceoff Win Rate']
            else:
                stats['faceoff_win_rate'] = 0

            # Shot accuracy
            if stats['total_shots'] > 0:
                stats['shot_accuracy'] = stats['shots']['total'] / stats['total_shots']
            else:
                stats['shot_accuracy'] = 0

            # Goals above expected
            stats['goals_above_expected'] = stats['goals']['total'] - stats['expected_goals']['total']

    return player_stats

def save_top_players_to_csv(player_stats, output_file_path):
    with open(output_file_path, 'w', newline='') as file:
        fieldnames = [
            'Player', 'Total Score', 'Goals', 'Expected Goals', 'Goals Above Expected',
            'Penalties', 'Faceoff Wins', 'Faceoff Win Rate',
            'Carried', 'Dumped', 'Total Entries', 'Successful Entries',
            'Denials', 'Entry Rate', 'Denial Rate', 'Carried Rate', 'Dumped Rate',
            'Shots', 'Shots on Net', 'Danger Zone Shots', 'Shot Accuracy'  # Added Shots on Net
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['total_score'], reverse=True)
        for player, stats in sorted_players[:10]:
            writer.writerow({
                'Player': player,
                'Total Score': round(stats['total_score'], 2),
                'Goals': stats['goals']['total'],
                'Expected Goals': round(stats['expected_goals']['total'], 2),
                'Goals Above Expected': round(stats['goals_above_expected'], 2),
                'Penalties': stats['penalties']['total'],
                'Faceoff Wins': stats['faceoff_wins']['total'],
                'Faceoff Win Rate': round(stats['faceoff_win_rate'] * 100, 1),
                'Carried': stats['carried']['total'],
                'Dumped': stats['dumped']['total'],
                'Total Entries': stats['total_entries'],
                'Successful Entries': stats['successful_entries'],
                'Denials': stats['denials'],
                'Entry Rate': round(stats['entry_rate'] * 100, 1),
                'Denial Rate': round(stats['denial_rate'] * 100, 1),
                'Carried Rate': round(stats['carried_rate'] * 100, 1),
                'Dumped Rate': round(stats['dumped_rate'] * 100, 1),
                'Shots': stats['shots']['total'],
                'Shots on Net': stats['shots_on_net']['total'],  # Added shots on net to output
                'Danger Zone Shots': stats['danger_zone_shots']['total'],
                'Shot Accuracy': round(stats['shot_accuracy'] * 100, 1)
            })
    print(f"Top players saved to {output_file_path}")

if __name__ == "__main__":
    # Filter data by date range
    start_date = '2018-02-11'
    end_date = '2018-02-21'
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    
    # Calculate and save player value scores
    player_stats = calculate_player_value_scores(filtered_file_path)
    save_top_players_to_csv(player_stats, output_file_path)