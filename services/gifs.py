from PIL import Image
import imagehash
import os
import shutil

# 📂 Input Paths
master_ref_path = r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\icons\CtmQ.gif"
frames_dir = r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\icons\ezgif-split (1)"

# 📂 Output Base Path (Where folders will be created)
output_base = r"C:\Users\Administrator\Desktop\ShannaCode\weq\weatherdashboard-shanna-noe\WeatherDashboard-Shanna\icons\sorted"

# 🏷️ Weather Labels from Grid Order (left to right, top to bottom)
grid_labels = [
    "sunny", "partly_cloudy", "night_clear",
    "night_cloudy", "cloudy", "snowy",
    "rainy", "foggy", "stormy",
    "hot", "rainbow"
]

# 🧠 Crop icons and hash for comparison
master_img = Image.open(master_ref_path).convert("RGB")
w, h = master_img.size
cols = 3
rows = 4
icon_w = w // cols
icon_h = h // rows

reference_hashes = {}

for idx, label in enumerate(grid_labels):
    row, col = divmod(idx, cols)
    left = col * icon_w
    upper = row * icon_h
    right = left + icon_w
    lower = upper + icon_h
    crop = master_img.crop((left, upper, right, lower))

    reference_hashes[label] = imagehash.phash(crop)

    # 📁 Create the folder if it doesn’t exist
    os.makedirs(os.path.join(output_base, label), exist_ok=True)
for frame_file in os.listdir(frames_dir):
    if frame_file.lower().endswith(".gif"):
        try:
            frame_path = os.path.join(frames_dir, frame_file)
            frame_img = Image.open(frame_path).convert("RGB")
            frame_hash = imagehash.phash(frame_img)

            best_label = min(reference_hashes, key=lambda lbl: frame_hash - reference_hashes[lbl])
            dest_folder = os.path.join(output_base, best_label)
            shutil.copy(frame_path, os.path.join(dest_folder, frame_file))

            print(f"✅ Sorted {frame_file} → {best_label}")
        except Exception as e:
            print(f"⚠️ Error processing {frame_file}: {e}")
