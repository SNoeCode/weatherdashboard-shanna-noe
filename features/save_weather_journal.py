from datetime import datetime

def save_journal_entry(city, mood, note, filepath="./data/journal.txt"):
    timestamp = datetime.now().isoformat()
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {city} | {mood} | {note}\n")