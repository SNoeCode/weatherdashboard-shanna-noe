from dateutil import parser
from zoneinfo import ZoneInfo
from datetime import timezone

def format_local_time(utc_iso: str, tz_name: str = "America/New_York") -> str:
    try:
        timestamp_utc = parser.isoparse(utc_iso)
        if timestamp_utc.tzinfo is None:
            timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)
        local_time = timestamp_utc.astimezone(ZoneInfo(tz_name))
        return local_time.strftime("%Y-%m-%d %I:%M %p %Z")
    except Exception as e:
        print(f"⚠️ Failed to convert time: {e}")
        return utc_iso

