import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
file_path = '/Users/joshuaolin/Desktop/Calgary/Pregamereport/filtered_prescout_dataset.csv'
data = pd.read_csv(file_path)

# Initialize the powerplay logic
def is_powerplay(row, home_skaters, away_skaters):
    is_powerplay = False
    home_team = row['Home Team']
    away_team = row['Away Team']
    team = row['Team']

    if team == home_team and home_skaters > away_skaters and away_skaters < 5:
        is_powerplay = True
    elif team == away_team and away_skaters > home_skaters and home_skaters < 5:
        is_powerplay = True
    return is_powerplay

# Filter for Canada's powerplay shots from the danger zone
canada_powerplay_shots = []

# Assuming data has columns 'X Coordinate', 'Y Coordinate', 'Event', 'Team', 'Home Team', 'Away Team', etc.
for index, row in data.iterrows():
    # Apply powerplay logic
    home_skaters = row['Home Team Skaters']
    away_skaters = row['Away Team Skaters']

    if row['Team'] == 'Olympic (Women) - Canada' and is_powerplay(row, home_skaters, away_skaters):
        # Check if the event is a shot and it's in the danger zone
        if row['Event'] == 'Shot' and 'X Coordinate' in row and 'Y Coordinate' in row:
            x_coord = float(row['X Coordinate'])
            y_coord = float(row['Y Coordinate'])

            # Danger zone shot logic
            if (11 <= x_coord <= 19.8 or (200 - 19.8) <= x_coord <= (200 - 11)) and 20.5 <= y_coord <= 64.4:
                canada_powerplay_shots.append((x_coord, y_coord))

# Convert the shot coordinates to a DataFrame
shots_df = pd.DataFrame(canada_powerplay_shots, columns=['X Coordinate', 'Y Coordinate'])

# Create a heatmap
plt.figure(figsize=(10, 6))
sns.kdeplot(x=shots_df['X Coordinate'], y=shots_df['Y Coordinate'], cmap="YlGnBu", fill=True)
plt.title("Heatmap of Canada's Powerplay Shots from the Danger Zone")
plt.xlabel("X Coordinate (Feet)")
plt.ylabel("Y Coordinate (Feet)")

# Show the plot
plt.show()
