import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the dataset
file_path = '/Users/joshuaolin/Desktop/Calgary/olympic_womens_dataset.csv'  # Update with correct path
data = pd.read_csv(file_path)

# Filter data for Brianne Jenner's shots
brianne_data = data[data['Player'] == 'Brianne Jenner']

# Get only the 'Shot' events and relevant X, Y coordinates
brianne_shots = brianne_data[brianne_data['Event'] == 'Shot']

# Extract X and Y coordinates of the shots
shots_df = brianne_shots[['X Coordinate', 'Y Coordinate']]

# Create a heatmap for the shot locations
plt.figure(figsize=(10, 6))
sns.kdeplot(x=shots_df['X Coordinate'], y=shots_df['Y Coordinate'], cmap="YlGnBu", fill=True)

plt.title("Shot Map for Brianne Jenner")
plt.xlabel("X Coordinate (Feet)")
plt.ylabel("Y Coordinate (Feet)")

# Show the plot
plt.show()
