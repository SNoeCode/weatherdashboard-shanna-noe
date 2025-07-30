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
            fetched_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
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
        query = """
        INSERT INTO readings (
            timestamp, city, country, temp, feels_like, humidity,
            pressure, weather_summary, weather_detail, wind_speed,
            wind_deg, clouds, visibility, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._conn() as conn:
                conn.execute(query, (
                    data['timestamp'],
                    data['city'],
                    data['country'],
                    data['temp'],
                    data['feels_like'],
                    data['humidity'],
                    data['pressure'],
                    data['weather_summary'],
                    data['weather_detail'],
                    data['wind_speed'],
                    data['wind_direction'],
                    data['cloudiness'],
                    data['visibility'],
                    data['api_timestamp']
                ))
            return True
        except sqlite3.Error as err:
            self.logger.error(f"[Insert Error] {err}\nData: {data}")
            return False

    def fetch_recent(self, city: str, country: str, hours: int = 24) -> List[Dict]:
        """
        Fetch recent weather readings for a city within specified hours
        """
        query = """
        SELECT timestamp, temp, humidity, pressure, weather_summary, weather_detail
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
                        'humidity': row[2],
                        'pressure': row[3],
                        'weather_summary': row[4],
                        'weather_detail': row[5]
                    })
                
                return readings
                
        except Exception as e:
            self.logger.error(f"Error fetching recent readings: {e}")
            return []

    # FIX: Add the missing get_recent_forecast method
    def get_recent_forecast(self, city: str, country: str, hours: int = 24) -> List[Dict]:
        """
        Get recent forecast data for a city. If no forecast data exists,
        fetch current weather as fallback.
        """
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
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM readings ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            if rows:
                headers = [description[0] for description in cursor.description]
                with open(output_file, mode="w", newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in rows:
                        writer.writerow(row)
                print(f"✅ Readings exported to {output_file}")
                return True
            else:
                print("⚠️ No readings to export.")
                return False
            
    # FIX: Update fetch_current_weather to accept the units parameter
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