import os
import logging
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

def setup_logger(name: str, level: str) -> logging.Logger:
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s — %(name)s — %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

@dataclass
class Config:
    api_key: str
    db_file_path: str
    logging_level: str = 'INFO'
    retry_limit: int = 3
    request_timeout: int = 10
    base_url: str = 'https://api.openweathermap.org/data/2.5'
    default_timezone: str = 'America/New_York'


    logger: Optional[logging.Logger] = None

    @classmethod
    def load_from_env(cls):
        api_key = os.getenv('WEATHER_API_KEY')
        if not api_key:
            raise ValueError('WEATHER_API_KEY environment variable required')

        db_file_path = os.getenv('DB_PATH')
        if not db_file_path:
            raise ValueError('DB_PATH environment variable required')

        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logger = setup_logger("WeatherApp", log_level)
        default_tz = os.getenv('DEFAULT_TIMEZONE', 'America/New_York')


        return cls(
            api_key=api_key,
            db_file_path=db_file_path,
            logging_level=log_level,
            retry_limit=int(os.getenv('MAX_RETRIES', '3')),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '10')),
            base_url=os.getenv('BASE_URL', 'https://api.openweathermap.org/data/2.5'),
            default_timezone=default_tz,
            logger=logger
        )