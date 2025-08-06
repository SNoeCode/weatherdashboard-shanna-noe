import os
import pandas as pd

# Folder containing your CSVs
folder_path = r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\weatherdata_group"

# File names
file_names = [
    "s_weather_data.csv",
    "t_weather_data.csv",
    "m_weather_data.csv",
    "v_weather_data.csv",
    "j_weather_data.csv"
]

# Container to hold extracted locations
locations = []

# Correct header names from your CSV
required_columns = ['City', 'State', 'Country']

for file_name in file_names:
    file_path = os.path.join(folder_path, file_name)
    try:
        df = pd.read_csv(file_path)

        if all(col in df.columns for col in required_columns):
            subset = df[required_columns].dropna()
            locations.extend(subset.to_dict(orient='records'))
        else:
            print(f"⚠️ Missing expected columns in {file_name}. Found: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error reading {file_name}: {e}")

# Show results
for loc in locations:
    print(f"{loc['City']}, {loc['State']}, {loc['Country']}")