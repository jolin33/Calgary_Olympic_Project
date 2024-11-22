import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
file_path = '/Users/joshuaolin/Desktop/Calgary/NewDraft/PlayerValueScore/filtered_playervaluescore_dataset.csv'
data = pd.read_csv(file_path)

# Identify top 2 players by total shots from the given dataset
top_players = ['Brianna Jenner', 'Marie-Philip Poulin']  # From your screenshot, these are the top 2

# Initialize the even strength logic
def is_even_strength(row, home_skaters, away_skaters):
    """Determine if the event is during even strength."""
    is_even_strength = False
    home_team = row['Home Team']
    away_team = row['Away Team']
    team = row['Team']

    if team == home_team and home_skaters == away_skaters:
        is_even_strength = True
    elif team == away_team and home_skaters == away_skaters:
        is_even_strength = True
    return is_even_strength

# Filter for even-strength shots from the top players
top_players_shots = []

# Iterate through the dataset to filter the shots of the top players
for index, row in data.iterrows():
    home_skaters = row['Home Team Skaters']
    away_skaters = row['Away Team Skaters']
    player = row['Player']

    if player in top_players and is_even_strength(row, home_skaters, away_skaters):
        if row['Event'] == 'Shot' and 'X Coordinate' in row and 'Y Coordinate' in row:
            x_coord = float(row['X Coordinate'])
            y_coord = float(row['Y Coordinate'])

            # Check if the shot is within the danger zone
            if (11 <= x_coord <= 19.8 or (200 - 19.8) <= x_coord <= (200 - 11)) and 20.5 <= y_coord <= 64.4:
                top_players_shots.append((x_coord, y_coord))

# Convert the shot coordinates to a DataFrame
shots_df = pd.DataFrame(top_players_shots, columns=['X Coordinate', 'Y Coordinate'])

# Create a heatmap for the total even-strength shots from the danger zone
plt.figure(figsize=(10, 6))
sns.kdeplot(x=shots_df['X Coordinate'], y=shots_df['Y Coordinate'], cmap="YlGnBu", fill=True)
plt.title("Heatmap of Even-Strength Shots from the Danger Zone (Top Players)")
plt.xlabel("X Coordinate (Feet)")
plt.ylabel("Y Coordinate (Feet)")

# Show the plot
plt.show()
