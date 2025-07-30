# def clean_weather_reading(r: dict, country: str = "US") -> Optional[dict]:
#     try:
#         if not isinstance(r, dict):
#             return None
#         temp_c = r.get("temp")
#         humidity = r.get("humidity")
#         pressure = r.get("pressure")
#         wind = r.get("wind_speed", 0.0)

#         temp_f = (temp_c) if country.upper() == "US" else temp_c

#         if (
#             isinstance(temp_f, (int, float)) and 50 <= temp_f <= 130 and
#             isinstance(humidity, (int, float)) and 0 <= humidity <= 100 and
#             isinstance(pressure, (int, float)) and 900 <= pressure <= 1100 and
#             isinstance(wind, (int, float)) and 0 <= wind <= 150
#         ):
#             return {
#                 "temp": round(temp_f, 1),
#                 "humidity": humidity,
#                 "pressure": pressure,
#                 "wind_speed": wind,
#                 "weather_summary": r.get("weather_summary", "Unknown"),
#                 "timestamp": r.get("timestamp")
#             }
#     except Exception:
#         pass
#     return None