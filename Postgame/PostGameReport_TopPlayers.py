import csv
from collections import defaultdict
import math

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Postgame/filtered_toppostgameplayers_dataset.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Postgame/toppostgameplayers.csv'

# Define weights for scoring
weights = {
    'Goal': {
        'evenstrength': 40,
        'powerplay': 30,
        'shorthanded': 50
    },
    'Expected Goals': {        
        'evenstrength': 5,
        'powerplay': 4,
        'shorthanded': 6
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
        'shorthanded': 5
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

def filter_data_by_date(file_path, filtered_path, game_date):
    """Filter the dataset for a specific game date and save to a new CSV."""
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row['game_date'] == game_date:
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

def initialize_player_stats(team):
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
        'expected_goals': 0,
        'expected_goals_weight': 0,
        'carried_rate': 0,
        'dumped_rate': 0,
        'carried_rate_weight': 0,
        'dumped_rate_weight': 0,
        'entry_rate': 0,
        'denial_rate': 0,
        'situations': defaultdict(int)
    }

def calculate_expected_goals(x_coord, y_coord, situation):
    """Calculate expected goals based on shot location and situation."""
    if x_coord > 100:
        x_coord = 200 - x_coord
        y_coord = 85 - y_coord
    
    distance = math.sqrt((x_coord - 0)**2 + (y_coord - 42.5)**2)
    angle = abs(math.atan2(y_coord - 42.5, x_coord))
    
    xg = 0.09
    xg *= 0.985 ** (distance/10)
    xg *= 0.985 ** (math.degrees(angle))
    
    is_danger_zone = ((11 <= x_coord <= 19.8 or 180.2 <= x_coord <= 188.8) and 
                    (20.5 <= y_coord <= 64.4))
    
    if is_danger_zone:
        xg *= 2.0
    
    situation_multiplier = {'evenstrength': 1.0, 'powerplay': 1.2, 'shorthanded': 0.8}
    xg *= situation_multiplier[situation]
    
    return xg, is_danger_zone

def calculate_player_value_scores(file_path):
    """Calculate player value scores for all players."""
    player_stats = {}

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            event_team = row['Team']
            home_team = row['Home Team']
            away_team = row['Away Team']
            event = row['Event']
            detail = row['Detail 1']
            detail_2 = row['Detail 2']
            player = row['Player']
            player2 = row['Player 2']

            situation = determine_game_situation(row, event_team)

            # Initialize players
            for p in [player, player2]:
                if p and p not in player_stats:
                    team = event_team if p == player else (home_team if event_team == away_team else away_team)
                    player_stats[p] = initialize_player_stats(team)

            if player:
                player_stats[player]['situations'][situation] += 1

                # Process events
                if event == 'Shot':
                    player_stats[player]['total_shots'] += 1
                    if detail_2 != 'Blocked':
                        player_stats[player]['shots'] += 1
                        player_stats[player]['total_score'] += weights['Shot'][situation]
                        
                        try:
                            x_coord = float(row['X Coordinate'])
                            y_coord = float(row['Y Coordinate'])
                            xg, is_danger_zone = calculate_expected_goals(x_coord, y_coord, situation)
                            
                            player_stats[player]['expected_goals'] += xg
                            player_stats[player]['expected_goals_weight'] += xg * weights['Expected Goals'][situation]
                            
                            if is_danger_zone:
                                player_stats[player]['danger_zone_shots'] += 1
                                player_stats[player]['total_score'] += weights['Danger Zone Shot'][situation]
                            
                        except (ValueError, TypeError):
                            pass

                elif event == 'Goal':
                    player_stats[player]['goals'] += 1
                    player_stats[player]['total_score'] += weights['Goal'][situation]
                elif event == 'Penalty Taken':
                    player_stats[player]['penalties'] += 1
                    player_stats[player]['total_score'] += weights['Penalty Taken'][situation]
                elif event == 'Puck Recovery':
                    player_stats[player]['total_score'] += weights['Puck Recovery'][situation]
                elif event == 'Faceoff Win':
                    player_stats[player]['faceoff_wins'] += 1
                    player_stats[player]['total_score'] += weights['Faceoff Win'][situation]
                    player_stats[player]['total_faceoffs'] += 1
                    if player2:
                        player_stats[player2]['total_faceoffs'] += 1
                elif event == 'Zone Entry':
                    player_stats[player]['total_entries'] += 1
                    if detail == 'Carried':
                        player_stats[player]['carried'] += 1
                        player_stats[player]['total_score'] += weights['Carried'][situation]
                        player_stats[player]['successful_entries'] += 1
                    elif detail == 'Dumped':
                        player_stats[player]['dumped'] += 1
                        player_stats[player]['total_score'] += weights['Dumped'][situation]
                        player_stats[player]['successful_entries'] += 1

                if event == 'Dump In/Out' and detail == 'Lost' and player2:
                    player_stats[player2]['denials'] += 1
                elif event in ['Incomplete Play', 'Takeaway'] and row['X Coordinate']:
                    try:
                        x_coord = float(row['X Coordinate'])
                        if 29 <= x_coord <= 207:
                            player_stats[player]['denials'] += 1
                    except ValueError:
                        pass

        # Calculate final rates and scores
        for stats in player_stats.values():
            stats['total_score'] += stats['expected_goals_weight']

            if stats['total_entries'] > 0:
                stats['entry_rate'] = stats['successful_entries'] / stats['total_entries']
                stats['denial_rate'] = stats['denials'] / stats['total_entries']
                stats['carried_rate'] = stats['carried'] / stats['total_entries']
                stats['dumped_rate'] = stats['dumped'] / stats['total_entries']
                
                stats['carried_rate_weight'] = stats['carried_rate'] * weights['Carried Rate']
                stats['dumped_rate_weight'] = stats['dumped_rate'] * weights['Dumped Rate']
                
                stats['total_score'] += (
                    stats['entry_rate'] * weights['Entry Rate'] +
                    stats['denial_rate'] * weights['Denial Rate'] +
                    stats['carried_rate_weight'] +
                    stats['dumped_rate_weight']
                )
            else:
                stats['entry_rate'] = stats['denial_rate'] = 0
                stats['carried_rate'] = stats['dumped_rate'] = 0
                stats['carried_rate_weight'] = stats['dumped_rate_weight'] = 0

            if stats['total_faceoffs'] > 0:
                stats['faceoff_win_rate'] = stats['faceoff_wins'] / stats['total_faceoffs']
                stats['total_score'] += stats['faceoff_win_rate'] * weights['Faceoff Win Rate']
            else:
                stats['faceoff_win_rate'] = 0

            stats['goals_above_expected'] = stats['goals'] - stats['expected_goals']

    return player_stats

def save_players_to_csv(player_stats, output_file_path):
    """Save player statistics to CSV file."""
    fieldnames = [
        'Player', 'Team', 'Total Score', 'Goals', 'Expected Goals', 'Expected Goals Weight',
        'Goals Above Expected', 'Penalties', 'Faceoff Wins', 'Faceoff Win Rate',
        'Carried', 'Dumped', 'Total Entries', 'Successful Entries',
        'Denials', 'Entry Rate', 'Denial Rate',
        'Shots', 'Danger Zone Shots', 'Shot Accuracy',
        'Carried Rate', 'Carried Rate Weight',  # Added rate metrics
        'Dumped Rate', 'Dumped Rate Weight'     # Added rate metrics
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
                'Expected Goals Weight': round(stats['expected_goals_weight'], 2),
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
                'Shot Accuracy': round((stats['shots'] / stats['total_shots'] * 100 if stats['total_shots'] > 0 else 0), 1),
                'Carried Rate': round(stats['carried_rate'] * 100, 1),
                'Carried Rate Weight': round(stats['carried_rate_weight'], 2),
                'Dumped Rate': round(stats['dumped_rate'] * 100, 1),
                'Dumped Rate Weight': round(stats['dumped_rate_weight'], 2)
            })
    print(f"Player stats saved to {output_file_path}")

if __name__ == "__main__":
    game_date = '2019-02-17'
    filter_data_by_date(original_file_path, filtered_file_path, game_date)
    player_stats = calculate_player_value_scores(filtered_file_path)
    save_players_to_csv(player_stats, output_file_path)