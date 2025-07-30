class WeatherEmoji:
   
    emoji_map = {
        "Clear": "☀️",
        "Rain": "🌧️",
        "Thunderstorm": "⛈️",
        "Clouds": "☁️",
        "Snow": "❄️",
        "Wind": "💨",
        "Mist": "🌫️",
        "Fog": "🌫️",
        "Haze": "🌫️",
        "Dust": "🌪️",
        "Sand": "🌪️",
        "Ash": "🌋",
        "Squall": "💨",
        "Tornado": "🌪️"
    }

    @classmethod
    def get_weather_emoji(cls, condition: str) -> str:
        return cls.emoji_map.get(condition.title(), "❓")