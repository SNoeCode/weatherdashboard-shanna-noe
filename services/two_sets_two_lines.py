import pandas as pd
import random
import os

weather_files = [
    r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\weatherdata_group\j_weather_data.csv",
    r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\weatherdata_group\m_weather_data.csv",
    r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\weatherdata_group\s_weather_data.csv",
    r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\weatherdata_group\t_weather_data.csv",
    r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\weatherdata_group\v_weather_data.csv"
]

def get_random_weather_data():
    # 🔀 Select 2 unique datasets
    selected_datasets = random.sample(weather_files, 2)
    
    weather_samples = []

    for file_path in selected_datasets:
        # 📥 Load CSV and sample 2 rows
        df = pd.read_csv(file_path)
        random_rows = df.sample(n=2)

        for _, row in random_rows.iterrows():
            weather_samples.append({
                'dataset': os.path.basename(file_path),  # Optional: filename identifier
                'data': row.to_dict()
            })
    
    return weather_samples