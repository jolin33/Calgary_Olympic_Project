import csv
from collections import defaultdict

# Define file paths
original_file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'
filtered_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Entry Defense Analysis/filtered_entry_defense_dataset.csv'
output_file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/Entry Defense Analysis/top_players_entry_defense_analysis.csv'

# Define weights for each event type
weights = {
    'Denial': 3,
    'Denial Rate': 150
}

# Step 1: Filter the data based on the date range
def filter_data_by_date(file_path, filtered_path, start_date, end_date):
    with open(file_path, 'r') as infile, open(filtered_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            game_date = row['game_date']
            if start_date <= game_date <= end_date:
                writer.writerow(row)

# Step 2: Calculate player entry defense scores with weights
def calculate_entry_defense_analysis(file_path):
    player_stats = {}
    player_games = defaultdict(set)  # Track unique games for each player

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames

        for row in reader:
            game_date = row['game_date']
            event = row['Event']
            detail = row['Detail 1']
            player = row['Player']
            opponent = row['Player 2']
            home_team = row['Home Team']
            away_team = row['Away Team']
            
            # Get coordinates
            try:
                x_coord = float(row['X Coordinate'])
            except ValueError:
                x_coord = None

            # Initialize players if not already in dictionary
            if player not in player_stats:
                player_stats[player] = {'total_score': 0, 'denials': 0, 'total_entries': 0, 'games_played': 0}
            if opponent not in player_stats:
                player_stats[opponent] = {'total_score': 0, 'denials': 0, 'total_entries': 0, 'games_played': 0}

            # Create unique game identifier
            game_id = f"{game_date}_{home_team}_{away_team}"

            # Count Zone Entries
            if event == 'Zone Entry' and detail in ['Carried', 'Dumped', 'Played']:
                if player:
                    player_stats[player]['total_entries'] += 1
                    player_games[player].add(game_id)

            # Case 1: Player attempts "Dump In/Out" and loses possession
            if event == 'Dump In/Out' and detail == 'Lost':
                if player and opponent:
                    player_stats[opponent]['denials'] += 1
                    player_stats[opponent]['total_score'] += weights['Denial']
                    player_games[player].add(game_id)
                    player_games[opponent].add(game_id)

            # Case 2: "Incomplete Play" event with coordinate check
            elif event == 'Incomplete Play' and x_coord is not None:
                if 29 <= x_coord <= 207:
                    if player and opponent:
                        player_stats[opponent]['denials'] += 1
                        player_stats[opponent]['total_score'] += weights['Denial']
                        player_games[player].add(game_id)
                        player_games[opponent].add(game_id)

            # Case 3: "Takeaway" event with coordinate check
            elif event == 'Takeaway' and x_coord is not None:
                if 29 <= x_coord <= 207:
                    if player:
                        player_stats[player]['denials'] += 1
                        player_stats[player]['total_score'] += weights['Denial']
                        player_games[player].add(game_id)

    # Update games played for each player based on unique game_ids
    for player in player_stats:
        player_stats[player]['games_played'] = len(player_games[player])

    # Calculate denial rates and adjust scores
    for player in player_stats:
        if player_stats[player]['total_entries'] > 0:
            denial_rate = player_stats[player]['denials'] / player_stats[player]['total_entries']
            denial_rate_weight = weights['Denial Rate'] * denial_rate
        else:
            denial_rate = 0
            denial_rate_weight = 0

        player_stats[player]['total_score'] += denial_rate_weight
        player_stats[player]['denial_rate'] = denial_rate

    return player_stats

# Step 3: Save the top players to a CSV file
def save_top_players_to_csv(player_stats, output_file_path, top_n=50):
    sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['total_score'], reverse=True)[:top_n]

    with open(output_file_path, 'w', newline='') as file:
        headers = 'Player,Total Score,Denials,Denial Rate,Games Played\n'
        file.write(headers)

        for player, stats in sorted_players:
            line = f"{player},{stats['total_score']},{stats['denials']},{stats['denial_rate']:.2f},{stats['games_played']}\n"
            file.write(line)
    print(f"Top {top_n} entry defense players saved to {output_file_path}")

# Main function to run the analysis
if __name__ == "__main__":
    start_date = '2018-02-11'
    end_date = '2018-02-21'
    
    # Step 1: Filter data by date range
    filter_data_by_date(original_file_path, filtered_file_path, start_date, end_date)
    
    # Step 2: Calculate player entry defense analysis
    best_players_analysis = calculate_entry_defense_analysis(filtered_file_path)
    
    # Step 3: Save the top players to CSV
    save_top_players_to_csv(best_players_analysis, output_file_path)