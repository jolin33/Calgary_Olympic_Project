
import csv
from collections import defaultdict

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Prescout/Prescoutfiltered.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Prescout/prescout_analysis.csv'

# Define goal probability constants
GOAL_PROBABILITIES = {
    'powerplay': {
        'danger_zone': 0.18,
        'non_danger': 0.09
    },
    'even_strength': {
        'danger_zone': 0.15,
        'non_danger': 0.07
    },
    'shorthanded': {
        'danger_zone': 0.12,
        'non_danger': 0.05
    }
}

# Define weights
weights = {
    'Goal': 4,
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
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            game_date = row['game_date']
            if start_date <= game_date <= end_date:
                writer.writerow(row)

def initialize_category_stats():
    """Initialize statistics for a single category."""
    return {
        'total_score': 0,
        'total_goals': 0,
        'total_carried': 0,
        'total_dumped': 0,
        'total_zone_entries': 0,
        'faceoff_wins': 0,
        'total_faceoffs': 0,
        'danger_zone_shots': 0,
        'successful_entries': 0,
        'entries': 0,
        'denials': 0,
        'shots': 0,
        'shots_on_net': 0,  # Added new counter for shots on net
        'non_danger_shots': 0,
        'expected_goals': 0,
        'takeaways': 0,
        'blocked': 0,
        'total_entries': 0,
        'powerplay_count': 0
    }

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
    return 'even_strength'

def calculate_powerplay_analysis(file_path):
    team_stats = defaultdict(lambda: {
        'shorthanded': initialize_category_stats(),
        'powerplay': initialize_category_stats(),
        'even_strength': initialize_category_stats()
    })
    
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

            game_id = f"{game_date}_{home_team}_{away_team}"
            if game_id != current_game:
                current_game = game_id

            situation = determine_game_situation(row, team)
            if situation == 'powerplay':
                pp_opportunities[team].add(game_id)

            stats = team_stats[team][situation]

            if event == 'Goal':
                stats['total_goals'] += 1
                stats['total_score'] += weights['Goal']
                
            elif event == 'Zone Entry':
                stats['entries'] += 1
                stats['total_zone_entries'] += 1
                stats['total_entries'] += 1

                if detail == 'Carried':
                    stats['total_carried'] += 1
                    stats['successful_entries'] += 1
                    stats['total_score'] += weights['Carried']
                elif detail == 'Dumped':
                    stats['total_dumped'] += 1
                    stats['successful_entries'] += 1
                    stats['total_score'] += weights['Dumped']
                    
            elif event == 'Faceoff Win':
                stats['faceoff_wins'] += 1
                stats['total_score'] += weights['Faceoff Win']
                stats['total_faceoffs'] += 1
                if player2:
                    opposing_team = away_team if team == home_team else home_team
                    team_stats[opposing_team][situation]['total_faceoffs'] += 1
            
            if detail == 'Lost':
                stats['denials'] += 1

            elif event == 'Takeaway':
                stats['takeaways'] += 1
                stats['total_score'] += weights['Takeaways']

            if event == 'Shot' and detail_2 == 'Blocked':
                blocking_team = away_team if team == home_team else home_team
                team_stats[blocking_team][situation]['blocked'] += 1
                team_stats[blocking_team][situation]['total_score'] += weights['Blocks']
            
            if event == 'Shot' and row['X Coordinate'] and row['Y Coordinate']:
                x_coord = float(row['X Coordinate'])
                y_coord = float(row['Y Coordinate'])
                stats['shots'] += 1
                
                # Add counter for shots on net
                if detail_2 == 'On Net':
                    stats['shots_on_net'] += 1

                is_danger_zone = ((11 <= x_coord <= 19.8 or 180.2 <= x_coord <= 188.8) and 
                                (20.5 <= y_coord <= 64.4))
                
                if is_danger_zone:
                    stats['danger_zone_shots'] += 1
                    stats['expected_goals'] += GOAL_PROBABILITIES[situation]['danger_zone']
                    stats['total_score'] += weights['Danger Zone Shot']
                else:
                    stats['non_danger_shots'] += 1
                    stats['expected_goals'] += GOAL_PROBABILITIES[situation]['non_danger']

    # Calculate rates and final scores
    for team_data in team_stats.values():
        for category, stats in team_data.items():
            # Zone entry rates
            if stats['total_zone_entries'] > 0:
                stats['carried_rate'] = stats['total_carried'] / stats['total_zone_entries']
                stats['dumped_rate'] = stats['total_dumped'] / stats['total_zone_entries']
                stats['carried_rate_weight'] = stats['carried_rate'] * weights['Carried Rate']
                stats['dumped_rate_weight'] = stats['dumped_rate'] * weights['Dumped Rate']
                stats['total_score'] += stats['carried_rate_weight'] + stats['dumped_rate_weight']
            
            # Entry and denial rates
            if stats['total_entries'] > 0:
                stats['entry_rate'] = stats['successful_entries'] / stats['total_entries']
                stats['denial_rate'] = stats['denials'] / stats['entries'] if stats['entries'] > 0 else 0
                stats['total_score'] += (stats['entry_rate'] * weights['Entry Rate'] +
                                       stats['denial_rate'] * weights['Denial Rate'])
            
            # Faceoff rates
            if stats['total_faceoffs'] > 0:
                stats['faceoff_win_rate'] = stats['faceoff_wins'] / stats['total_faceoffs']
                stats['total_score'] += stats['faceoff_win_rate'] * weights['Faceoff Win Rate']

            # Expected goals contribution
            stats['total_score'] += stats['expected_goals'] * weights['Expected Goals']
            stats['goals_above_expected'] = stats['total_goals'] - stats['expected_goals']

            # Shot danger rate
            if stats['shots'] > 0:
                stats['shot_danger_rate'] = stats['danger_zone_shots'] / stats['shots']

        # Calculate PP success rate for powerplay category
        team_data['powerplay']['pp_opportunities'] = len(pp_opportunities[team])
        if team_data['powerplay']['pp_opportunities'] > 0:
            team_data['powerplay']['pp_success_rate'] = (team_data['powerplay']['total_goals'] / 
                                                       team_data['powerplay']['pp_opportunities'])
            success_score = team_data['powerplay']['pp_success_rate'] * weights['PP Success Rate']
            team_data['powerplay']['total_score'] += success_score

    return team_stats

def save_top_teams_to_csv(team_stats, output_file_path):
    with open(output_file_path, 'w', newline='') as file:
        fieldnames = [
            'Team', 'Category', 'Goals', 'Expected Goals', 'Goals vs Expected', 
            'Entries', 'Successful Entries', 'Entry Rate',
            'Denials', 'Denial Rate', 'Total Entries',
            'Faceoff Wins', 'Total Faceoffs', 'Faceoff Win Rate',
            'Shots', 'Shots on Net', 'Danger Zone Shots', 'Non-Danger Shots', 'Shot Danger Rate',  # Added 'Shots on Net'
            'Takeaways', 'Blocked',
            'Total Score', 'PP Opportunities', 'PP Success Rate',
            'Carried', 'Dumped', 'Carried Rate', 'Dumped Rate',
            'Carried Rate Weight', 'Dumped Rate Weight'
        ]
        writer = csv.writer(file)
        writer.writerow(fieldnames)

        for team, categories in sorted(team_stats.items()):
            for category, stats in categories.items():
                row_data = [
                    team,
                    category,
                    stats['total_goals'],
                    f"{stats['expected_goals']:.2f}",
                    f"{stats['goals_above_expected']:.2f}",
                    stats['entries'],
                    stats['successful_entries'],
                    f"{stats['entry_rate']:.2f}" if 'entry_rate' in stats else "0.00",
                    stats['denials'],
                    f"{stats['denial_rate']:.2f}" if 'denial_rate' in stats else "0.00",
                    stats['total_entries'],
                    stats['faceoff_wins'],
                    stats['total_faceoffs'],
                    f"{stats['faceoff_win_rate']:.2f}" if 'faceoff_win_rate' in stats else "0.00",
                    stats['shots'],
                    stats['shots_on_net'],  # Added shots on net to output
                    stats['danger_zone_shots'],
                    stats['non_danger_shots'],
                    f"{stats['shot_danger_rate']:.2f}" if 'shot_danger_rate' in stats else "0.00",
                    stats['takeaways'],
                    stats['blocked'],
                    f"{stats['total_score']:.2f}",
                    stats.get('pp_opportunities', 0),
                    f"{stats.get('pp_success_rate', 0):.2f}",
                    stats['total_carried'],
                    stats['total_dumped'],
                    f"{stats.get('carried_rate', 0):.2f}",
                    f"{stats.get('dumped_rate', 0):.2f}",
                    f"{stats.get('carried_rate_weight', 0):.2f}",
                    f"{stats.get('dumped_rate_weight', 0):.2f}"
                ]
                writer.writerow(row_data)

    print(f"Team analysis saved to {output_file_path}")

if __name__ == "__main__":
    start_date = '2018-02-11'
    end_date = '2018-02-21'
    
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    team_stats = calculate_powerplay_analysis(filtered_file_path)
    save_top_teams_to_csv(team_stats, output_file_path)