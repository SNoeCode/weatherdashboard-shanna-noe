import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Generator
from contextlib import contextmanager
import csv
import os
import logging
from dotenv import load_dotenv
from weather_data_fetcher import WeatherDataFetcher
load_dotenv()

class WeatherDB:
    def __init__(self, fetcher: Optional['WeatherDataFetcher'] = None):
        db_path = os.getenv("DB_PATH")
        if not db_path:
            raise ValueError("Environment variable DB_PATH is not set.")
        self.db_file = Path(db_path)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize database schema
        self._initialize_schema()
        self.fetcher = fetcher
    def _conn(self):
      return sqlite3.connect(str(self.db_file))

    def _initialize_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            state TEXT,
            temp REAL NOT NULL,
            feels_like REAL,
            humidity INTEGER,
            pressure REAL,
            weather_summary TEXT,
            weather_detail TEXT,
            wind_speed REAL,
            wind_deg INTEGER,
            clouds INTEGER,
            visibility INTEGER,
            precipitation REAL DEFAULT 0,
            sunrise TEXT,
            sunset TEXT,
            fetched_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            state TEXT,
            lat REAL,
            lon REAL,
            tz TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city, country)
        );

        CREATE TABLE IF NOT EXISTS request_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            url TEXT NOT NULL,
            location_id INTEGER,
            status TEXT NOT NULL,
            error TEXT,
            latency_ms INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(id)
        );

        CREATE INDEX IF NOT EXISTS idx_readings_time ON readings(timestamp);
        CREATE INDEX IF NOT EXISTS idx_readings_location ON readings(city, country);
        CREATE INDEX IF NOT EXISTS idx_log_time ON request_log(timestamp);
        """
        with self._conn() as conn:
            conn.executescript(schema)

            # Check and add missing columns if necessary
            required_columns = [
                ('state', 'TEXT DEFAULT ""'),
                ('temp_min', 'REAL'),
                ('temp_max', 'REAL'),
                ('precipitation', 'REAL DEFAULT 0'),
                ('sunrise', 'TEXT DEFAULT ""'),
                ('sunset', 'TEXT DEFAULT ""')
            ]

            # Get existing columns in the readings table
            cursor = conn.execute("PRAGMA table_info(readings)")
            existing_columns = [row[1] for row in cursor.fetchall()]

            for column_name, column_def in required_columns:
                if column_name not in existing_columns:
                    try:
                        conn.execute(f"ALTER TABLE readings ADD COLUMN {column_name} {column_def}")
                        self.logger.info(f"Added column '{column_name}' to readings table")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e).lower():
                            self.logger.error(f"Error adding column {column_name}: {e}")



    # def _conn(self):
    #     return sqlite3.connect(str(self.db_file))

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def insert_reading(self, data: Dict) -> bool:
        """Insert weather reading with all fields including highs/lows"""
        query = """
        INSERT INTO readings (
            timestamp, city, country, state, temp, temp_min, temp_max, feels_like, humidity,
            pressure, weather_summary, weather_detail, wind_speed,
            wind_deg, clouds, visibility, precipitation, sunrise, sunset, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._conn() as conn:
                conn.execute(query, (
                    data['timestamp'],
                    data['city'],
                    data['country'],
                    data.get('state', ''),
                    data['temp'],
                    data.get('temp_min', data['temp']),  # Default to current temp if no min
                    data.get('temp_max', data['temp']),  # Default to current temp if no max
                    data['feels_like'],
                    data['humidity'],
                    data['pressure'],
                    data['weather_summary'],
                    data['weather_detail'],
                    data['wind_speed'],
                    data['wind_direction'],
                    data['cloudiness'],
                    data['visibility'],
                    data.get('precipitation', 0),
                    data.get('sunrise', ''),
                    data.get('sunset', ''),
                    data['api_timestamp']
                ))
            return True
        except sqlite3.Error as err:
            self.logger.error(f"[Insert Error] {err}\nData: {data}")
            return False
        
    def fetch_recent(self, city: str, country: str, hours: int = 24) -> List[Dict]:
       
        query = """
        SELECT timestamp, temp, temp_min, temp_max, humidity, pressure, weather_summary, weather_detail
        FROM readings 
        WHERE city = ? AND country = ?
        AND datetime(timestamp) >= datetime('now', '-{} hours')
        ORDER BY timestamp DESC
        """.format(hours)
        
        try:
            with self._conn() as conn:
                cursor = conn.execute(query, (city, country))
                results = cursor.fetchall()
                
                readings = []
                for row in results:
                    readings.append({
                        'timestamp': row[0],  
                        'temp': row[1],
                        'temp_min': row[2],
                        'temp_max': row[3],
                        'humidity': row[4],
                        'pressure': row[5],
                        'weather_summary': row[6],
                        'weather_detail': row[7]
                    })
                
                return readings
                
        except Exception as e:
            self.logger.error(f"Error fetching recent readings: {e}")
            return []
    def get_recent_forecast(self, city: str, country: str, hours: int = 24) -> List[Dict]:
        if not self.fetcher:
            self.logger.warning("No fetcher available for forecast data")
            return []
        
        try:
            # Try to get forecast data from the fetcher
            forecast_data = self.fetcher.fetch_recent(city, country, hours)
            if forecast_data:
                return forecast_data
            
            # Fallback to current weather if no forecast available
            current = self.fetch_current_weather(city, country)
            if current:
                return [current]
                
        except Exception as e:
            self.logger.error(f"Error getting recent forecast: {e}")
            
        return []
            
    def get_error_log(self, limit=20) -> List[Dict]:
        query = """
        SELECT timestamp, city, country, status, error
        FROM request_log
        JOIN locations ON request_log.location_id = locations.id
        WHERE status != 'success'
        ORDER BY timestamp DESC
        LIMIT ?
        """
        with self.get_connection() as conn:
            return [dict(row) for row in conn.execute(query, (limit,))]

    def update_location(self, city: str, country: str, **kwargs) -> None:
        with self._conn() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO locations (id, city, country, lat, lon, tz, is_active)
            VALUES (
                COALESCE((SELECT id FROM locations WHERE city = ? AND country = ?), NULL),
                ?, ?, ?, ?, ?, ?
            )
            """, (
                city, country,
                city, country,
                kwargs.get('latitude'),
                kwargs.get('longitude'),
                kwargs.get('timezone'),
                int(kwargs.get('is_active', True))
            ))
    
    def get_all_readings(self) -> List[Dict]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM readings ORDER BY timestamp DESC").fetchall()
            return [dict(row) for row in rows]
        
    def get_all_locations(self) -> List[Dict]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM locations ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]        
    
    def export_locations_to_csv(self, output_file: str = "./data/weather_data.csv") -> bool:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM locations")
            rows = cursor.fetchall()
            if rows:
                headers = [description[0] for description in cursor.description]
                with open(output_file, mode="w", newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in rows:
                        writer.writerow(row)
                print(f"✅ Location data exported to {output_file}")
                return True
            else:
                print("⚠️ No location data to export.")
                return False
            
    def export_readings_to_csv(self, output_file: str = "./data/weather_readings.csv") -> bool:
        """Export readings in the format: Current Time,City,State,Country,Temperature,Feels Like,Humidity,Precipitation,Pressure,Wind Speed,Wind Direction,Visibility,Sunrise,Sunset"""
        dir_path = os.path.dirname(output_file)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM readings ORDER BY timestamp DESC")
            rows = cursor.fetchall()

            if rows:
                new_headers = [
                    "Current Time", "City", "State", "Country", "Temperature", 
                    "Feels Like", "Humidity", "Precipitation", "Pressure", 
                    "Wind Speed", "Wind Direction", "Visibility", "Sunrise", "Sunset"
                ]
                
                with open(output_file, mode="w", newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(new_headers)
                    
                    for row in rows:
                        row_dict = dict(zip([description[0] for description in cursor.description], row))
                        
                        # Format timestamp as mm-dd-yy hh:mm:ss
                        try:
                            if row_dict.get('timestamp'):
                                dt = datetime.fromisoformat(row_dict['timestamp'].replace('Z', '+00:00'))
                                formatted_time = dt.strftime("%m-%d-%y %H:%M:%S")
                            else:
                                formatted_time = ""
                        except:
                            formatted_time = row_dict.get('timestamp', '')
                        
                        # Format sunrise/sunset times
                        sunrise_formatted = ""
                        sunset_formatted = ""
                        if row_dict.get('sunrise'):
                            try:
                                sunrise_dt = datetime.fromisoformat(row_dict['sunrise'].replace('Z', '+00:00'))
                                sunrise_formatted = sunrise_dt.strftime("%H:%M:%S")
                            except:
                                sunrise_formatted = row_dict.get('sunrise', '')
                        
                        if row_dict.get('sunset'):
                            try:
                                sunset_dt = datetime.fromisoformat(row_dict['sunset'].replace('Z', '+00:00'))
                                sunset_formatted = sunset_dt.strftime("%H:%M:%S")
                            except:
                                sunset_formatted = row_dict.get('sunset', '')
                        
                        new_row = [
                            formatted_time,                           # Current Time
                            row_dict.get('city', ''),               # City
                            row_dict.get('state', ''),              # State
                            row_dict.get('country', ''),            # Country
                            row_dict.get('temp', ''),               # Temperature
                            row_dict.get('feels_like', ''),         # Feels Like
                            row_dict.get('humidity', ''),           # Humidity
                            row_dict.get('precipitation', ''),      # Precipitation
                            row_dict.get('pressure', ''),           # Pressure
                            row_dict.get('wind_speed', ''),         # Wind Speed
                            row_dict.get('wind_deg', ''),           # Wind Direction
                            row_dict.get('visibility', ''),         # Visibility
                            sunrise_formatted,                       # Sunrise
                            sunset_formatted                         # Sunset
                        ]
                        writer.writerow(new_row)
                        
                print(f"✅ Readings exported to {os.path.abspath(output_file)}")
                return True
            else:
                print("⚠️ No readings to export.")
                return False
    def fetch_current_weather(self, city: str, country: str, units: str = 'imperial') -> Optional[Dict]:
        """
        Fetch current weather using the WeatherDataFetcher
        Now accepts units parameter to match the expected signature
        """
        if not self.fetcher:
            raise RuntimeError("No WeatherDataFetcher provided to WeatherDB.")
        
        # Use imperial units for US cities by default
        if country.upper() == "US" and units == 'imperial':
            units = 'imperial'
        elif country.upper() != "US" and units == 'imperial':
            units = 'metric'
            
        data = self.fetcher.fetch_current_weather(city, country, units)
        if data:
            self.insert_reading(data)
        return data
    
    def log_request(self, url: str, location_id: Optional[int], status: str,
                    error: Optional[str] = None, latency_ms: Optional[int] = None) -> None:
        """Log API request details for monitoring and debugging"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                INSERT INTO request_log (
                    timestamp, url, location_id, status, error, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    url,
                    location_id,
                    status,
                    error,
                    latency_ms
                ))
        except Exception as e:
            self.logger.error(f"Failed to log request: {e}")

    def get_location_id(self, city: str, country: str) -> Optional[int]:

        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM locations WHERE city = ? AND country = ?",
                    (city, country)
                )
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            self.logger.error(f"Error getting location ID: {e}")
            return None
    def save_weather_entry(self, row_data: dict):
        try:
            self.insert_reading(row_data)  # Use your existing insert method
        except Exception as e:
            logging.error(f"Error saving weather entry: {e}")