import csv
from collections import defaultdict

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Entry Defense Analysis/filtered_team_tradeoff_dataset.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Entry Defense Analysis/team_tradeoff_analysis.csv'

# Step 1: Filter the data based on the date range
def filter_data_by_date(file_path, filtered_path, start_date, end_date):
    """Filter the CSV data by a specified date range."""
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            game_date = row['game_date']
            if start_date <= game_date <= end_date:
                writer.writerow(row)

# Step 2: Calculate the tradeoff score for each team
def calculate_tradeoff_score(file_path):
    """Calculate the tradeoff score for each team."""
    team_stats = defaultdict(lambda: {'denials': 0, 'total_entries': 0, 'opponent_shots': 0, 'opponent_possessions': 0})
    data = []

    # Read data from filtered CSV file
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            home_team = row['Home Team']
            away_team = row['Away Team']
            event_team = row['Team']
            event = row['Event']
            detail = row['Detail 1']
            
            # Get opponent team
            opponent_team = away_team if event_team == home_team else home_team
            
            # Get coordinates if relevant
            try:
                x_coord = float(row['X Coordinate'])
            except ValueError:
                x_coord = None

            # Count Zone Entries
            if event == 'Zone Entry' and detail in ['Carried', 'Dumped', 'Played']:
                team_stats[event_team]['total_entries'] += 1

            # Track entry denial events (keeping original logic)
            if event in ['Dump In/Out', 'Incomplete Play', 'Takeaway']:
                if event == 'Dump In/Out' and detail == 'Lost':
                    team_stats[event_team]['denials'] += 1
                elif event == 'Incomplete Play' and x_coord is not None and 29 <= x_coord <= 207:
                    team_stats[event_team]['denials'] += 1
                elif event == 'Takeaway' and x_coord is not None and 29 <= x_coord <= 207:
                    team_stats[event_team]['denials'] += 1

            # Track opponent's offensive metrics
            if event_team != opponent_team:
                if event == 'Shot':
                    team_stats[opponent_team]['opponent_shots'] += 1
                if event in ['Zone Entry', 'Puck Possession']:
                    team_stats[opponent_team]['opponent_possessions'] += 1

    # Calculate metrics and tradeoff score for each team
    for team, stats in team_stats.items():
        if stats['total_entries'] > 0 and stats['opponent_possessions'] > 0:
            denial_rate = stats['denials'] / stats['total_entries']
            offense_limiting_rate = 1 - (stats['opponent_shots'] / stats['opponent_possessions'])
            tradeoff_score = (denial_rate - offense_limiting_rate) ** 2

            data.append({
                'Team': team,
                'Denials': stats['denials'],
                'Total Entries': stats['total_entries'],
                'Denial Rate': round(denial_rate, 2),
                'Opponent Shots': stats['opponent_shots'],
                'Opponent Possessions': stats['opponent_possessions'],
                'Offense Limiting Rate': round(offense_limiting_rate, 2),
                'Tradeoff Score': round(tradeoff_score, 4)
            })

    return data

# Step 3: Save the metrics to a CSV file for visualization
def save_tradeoff_scores_to_csv(data, output_file):
    """Save the tradeoff scores to a CSV file."""
    with open(output_file, 'w', newline='') as file:
        headers = ['Team', 'Denials', 'Total Entries', 'Denial Rate', 
                   'Opponent Shots', 'Opponent Possessions', 'Offense Limiting Rate', 'Tradeoff Score']
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Tradeoff scores saved to {output_file}")

if __name__ == "__main__":
    # Define the date range
    start_date = '2018-02-11'
    end_date = '2018-02-21'
    
    # Step 1: Filter data by date range
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    
    # Step 2: Calculate tradeoff scores using the filtered data
    teams_metrics = calculate_tradeoff_score(filtered_file_path)
    
    # Step 3: Save the results to CSV
    save_tradeoff_scores_to_csv(teams_metrics, output_file_path)