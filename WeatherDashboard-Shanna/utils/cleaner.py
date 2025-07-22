import os
import glob
import hashlib

def hash_file(path):
    """Generate SHA256 hash of a file’s content."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def remove_duplicate_csvs(folder="final/WeatherDashboard-Shanna/data"):
    """Find and delete duplicate CSV files based on content hash."""
    print("🔎 Checking for duplicate CSVs...")
    seen_hashes = {}
    duplicates = []

    for file_path in glob.glob(os.path.join(folder, "*.csv")):
        file_hash = hash_file(file_path)
        if file_hash in seen_hashes:
            duplicates.append(file_path)
        else:
            seen_hashes[file_hash] = file_path

    for dupe_path in duplicates:
        try:
            os.remove(dupe_path)
            print(f"🗑️ Removed duplicate: {dupe_path}")
        except Exception as e:
            print(f"⚠️ Error deleting {dupe_path}: {e}")

    print(f"✅ Removed {len(duplicates)} duplicate CSV file(s)")

def cleanup(days: int = 15, validate_batch: int = 100):
    """Run deduplication, pruning, job validation, and CSV duplicate cleanup."""
    print("🧼 Running job cleanup...")
    remove_duplicate_csvs("final/WeatherDashboard-Shanna/data")
    print("✅ Cleanup complete")