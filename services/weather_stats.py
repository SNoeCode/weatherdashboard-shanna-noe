from datetime import datetime, timedelta
import csv
import logging
from typing import Dict, Optional, List
from config import Config

def get_weather_stats(db, city: str, state: str = "", country: str = "US", days: int = 7) -> Dict:
    """
    Enhanced weather statistics with better data handling and validation
    """
    logger = logging.getLogger(__name__)
    hours = days * 24
    
    try:
        # Try multiple methods to get data
        readings = []
        
        # Method 1: Try fetch_recent
        try:
            readings = db.fetch_recent(city, country, hours)
            logger.info(f"Method 1 - fetch_recent: Found {len(readings)} readings")
        except Exception as e:
            logger.warning(f"fetch_recent failed: {e}")
        
        # Method 2: If no data, try get_all_readings and filter
        if not readings:
            try:
                all_readings = db.get_all_readings()
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                readings = []
                for reading in all_readings:
                    try:
                        # Handle different timestamp formats
                        timestamp_str = reading.get('timestamp', '')
                        if isinstance(timestamp_str, str):
                            if 'T' in timestamp_str:
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            timestamp = timestamp_str
                        
                        # Check location match
                        reading_city = reading.get('city', '').lower()
                        reading_country = reading.get('country', '').lower()
                        
                        if (reading_city == city.lower() and 
                            reading_country == country.lower() and 
                            timestamp >= cutoff_time):
                            readings.append(reading)
                    except Exception as parse_error:
                        logger.debug(f"Error parsing reading: {parse_error}")
                        continue
                
                logger.info(f"Method 2 - filtered readings: Found {len(readings)} readings")
            except Exception as e:
                logger.warning(f"get_all_readings failed: {e}")
        
        # Method 3: Try to get current weather if no historical data
        if not readings:
            try:
                current_weather = db.fetch_current_weather(city, country)
                if current_weather:
                    readings = [current_weather]
                    logger.info(f"Method 3 - current weather: Found 1 reading")
            except Exception as e:
                logger.warning(f"fetch_current_weather failed: {e}")
        
        logger.info(f"Total readings found for {city}, {country}: {len(readings)}")
        
        if not readings:
            # Return empty stats structure
            stats = {
                "avg_temp": "N/A", "min_temp": "N/A", "max_temp": "N/A", "temp_range": "N/A",
                "humidity_avg": "N/A", "humidity_min": "N/A", "humidity_max": "N/A",
                "pressure_avg": "N/A", "wind_avg": "N/A", "wind_min": "N/A", "wind_max": "N/A",
                "common_conditions": "N/A", "condition_count": "N/A",
                "total_readings": 0, "period_days": days,
                "temp_unit": "°F" if country.upper() == "US" else "°C",
                "coverage_percentage": 0, "data_quality": "Missing",
                "last_updated": "N/A"
            }
        else:
            # Process the readings
            temps = []
            humidities = []
            pressures = []
            winds = []
            conditions = []
            
            for reading in readings:
                # Temperature
                temp = reading.get("temp")
                if temp is not None and isinstance(temp, (int, float)):
                    # Convert to Fahrenheit if needed
                    if country.upper() == "US":
                        if temp < 50:  # Assume it's Celsius and convert
                            temp = (temp * 9/5) + 32
                    temps.append(float(temp))
                
                # Humidity
                humidity = reading.get("humidity")
                if humidity is not None and isinstance(humidity, (int, float)):
                    humidities.append(float(humidity))
                
                # Pressure
                pressure = reading.get("pressure")
                if pressure is not None and isinstance(pressure, (int, float)):
                    pressures.append(float(pressure))
                
                # Wind speed
                wind_speed = reading.get("wind_speed")
                if wind_speed is not None and isinstance(wind_speed, (int, float)):
                    winds.append(float(wind_speed))
                
                # Weather conditions
                condition = reading.get("weather_summary") or reading.get("weather_detail")
                if condition and isinstance(condition, str):
                    conditions.append(condition.title())
            
            # Calculate statistics
            stats = {
                "total_readings": len(readings),
                "period_days": days,
                "temp_unit": "°F" if country.upper() == "US" else "°C",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Temperature stats
            if temps:
                stats.update({
                    "avg_temp": round(sum(temps) / len(temps), 1),
                    "min_temp": round(min(temps), 1),
                    "max_temp": round(max(temps), 1),
                    "temp_range": round(max(temps) - min(temps), 1)
                })
            else:
                stats.update({
                    "avg_temp": "N/A", "min_temp": "N/A", "max_temp": "N/A", "temp_range": "N/A"
                })
            
            # Humidity stats
            if humidities:
                stats.update({
                    "humidity_avg": round(sum(humidities) / len(humidities), 1),
                    "humidity_min": round(min(humidities), 1),
                    "humidity_max": round(max(humidities), 1)
                })
            else:
                stats.update({
                    "humidity_avg": "N/A", "humidity_min": "N/A", "humidity_max": "N/A"
                })
            
            # Pressure stats
            if pressures:
                stats["pressure_avg"] = round(sum(pressures) / len(pressures), 1)
            else:
                stats["pressure_avg"] = "N/A"
            
            # Wind stats
            if winds:
                stats.update({
                    "wind_avg": round(sum(winds) / len(winds), 1),
                    "wind_min": round(min(winds), 1),
                    "wind_max": round(max(winds), 1)
                })
            else:
                stats.update({
                    "wind_avg": "N/A", "wind_min": "N/A", "wind_max": "N/A"
                })
            
            # Condition stats
            if conditions:
                from collections import Counter
                condition_counter = Counter(conditions)
                most_common = condition_counter.most_common(1)[0]
                stats.update({
                    "common_conditions": most_common[0],
                    "condition_count": len(set(conditions))
                })
            else:
                stats.update({
                    "common_conditions": "N/A",
                    "condition_count": "N/A"
                })
            
            # Data quality assessment
            expected_readings = hours  # One reading per hour would be ideal
            coverage = min(100.0, (len(readings) / expected_readings) * 100)
            stats["coverage_percentage"] = round(coverage, 1)
            
            if coverage > 80:
                stats["data_quality"] = "Excellent"
            elif coverage > 60:
                stats["data_quality"] = "Good"
            elif coverage > 30:
                stats["data_quality"] = "Fair"
            else:
                stats["data_quality"] = "Poor"
        
        # Save to CSV and database
        try:
            row = format_weather_row(stats, city, state, country)
            save_to_csv(row)
            save_to_database(db, row)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
        
        logger.info(f"✅ Generated stats for {city}, {country}: {stats['total_readings']} readings")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating weather stats: {e}")
        # Return error stats
        return {
            "avg_temp": "Error", "min_temp": "Error", "max_temp": "Error", "temp_range": "Error",
            "humidity_avg": "Error", "humidity_min": "Error", "humidity_max": "Error",
            "pressure_avg": "Error", "wind_avg": "Error", "wind_min": "Error", "wind_max": "Error",
            "common_conditions": "Error", "condition_count": "Error",
            "total_readings": 0, "period_days": days,
            "temp_unit": "°F" if country.upper() == "US" else "°C",
            "coverage_percentage": 0, "data_quality": "Error",
            "last_updated": "Error"
        }

def format_weather_row(stats: dict, city: str, state: str, country: str) -> dict:
    """Format stats data for CSV export"""
    now = datetime.now().strftime("%m-%d-%y %H:%M:%S")
    return {
        "Timestamp": now,
        "City": city,
        "State": state,
        "Country": country,
        "Temperature": stats.get("avg_temp", "N/A"),
        "Feels Like": stats.get("avg_temp", "N/A"),
        "Humidity": stats.get("humidity_avg", "N/A"),
        "Precipitation": "N/A",
        "Pressure": stats.get("pressure_avg", "N/A"),
        "Wind Speed": stats.get("wind_avg", "N/A"),
        "Wind Direction": "N/A",
        "Visibility": "N/A",
        "Sunrise": "N/A",
        "Sunset": "N/A",
        "Data Quality": stats.get("data_quality", "Unknown"),
        "Total Readings": stats.get("total_readings", 0)
    }

def save_to_csv(row_data: dict, filename="weather_log.csv"):
    """Save weather data to CSV file with error handling"""
    fieldnames = list(row_data.keys())
    try:
        with open(filename, mode="a", newline="", encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(row_data)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error writing to CSV: {e}")

def save_to_database(db, row_data: dict):
    """Save weather stats to database"""
    try:
        if hasattr(db, 'save_weather_entry'):
            db.save_weather_entry(row_data)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error writing to DB: {e}")

def debug_database_contents(db, city: str, country: str):
    """Debug function to inspect database contents"""
    logger = logging.getLogger(__name__)
    
    try:
        # Check all readings
        all_readings = db.get_all_readings()
        logger.info(f"Total readings in database: {len(all_readings)}")
        
        # Check for specific city
        city_readings = [r for r in all_readings 
                        if r.get('city', '').lower() == city.lower() 
                        and r.get('country', '').lower() == country.lower()]
        logger.info(f"Readings for {city}, {country}: {len(city_readings)}")
        
        # Show sample data
        if city_readings:
            sample = city_readings[0]
            logger.info(f"Sample reading: {sample}")
        
        # Check recent data
        recent = db.fetch_recent(city, country, 48)
        logger.info(f"Recent readings (48h): {len(recent)}")
        
    except Exception as e:
        logger.error(f"Error debugging database: {e}")