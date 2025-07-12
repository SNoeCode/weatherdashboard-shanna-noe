import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

def draw_wireframe_layout():
    # Create canvas
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 1000)
    ax.set_ylim(700, 0) 
    ax.set_facecolor("#f7fbff")
    ax.axis("off")

    # SearchBar
    ax.add_patch(patches.Rectangle((50, 630), 900, 40, edgecolor="black", facecolor="white"))
    ax.text(60, 650, "SearchBar — City, Country, Get Weather", fontsize=10, fontweight="bold")

    # ViewToggle + Buttons
    ax.add_patch(patches.Rectangle((50, 580), 900, 40, edgecolor="black", facecolor="white"))
    ax.text(60, 600, "ViewToggle — Save to Favorites / Save to CSV", fontsize=10)

    # Current Weather
    ax.add_patch(patches.Rectangle((50, 510), 900, 60, edgecolor="black", facecolor="#e6f7ff"))
    ax.text(60, 540, "Current Weather — Icon | Temp (°F/°C) | Condition Summary", fontsize=10)

    # Forecast Cards
    ax.text(60, 420, "Forecast Section — 5 Cards (Date, Icon, Temp, Summary)", fontsize=10)
    for i in range(5):
        x = 60 + i * 180
        ax.add_patch(patches.Rectangle((x, 370), 140, 80, edgecolor="gray", facecolor="#e6f7ff"))
        ax.text(x + 70, 410, f"Card {i+1}", fontsize=8, ha="center")

    # Favorites Dashboard
    ax.add_patch(patches.Rectangle((50, 80), 900, 260, edgecolor="black", facecolor="#e6f7ff"))
    ax.text(60, 320, "Favorites Tab — City Info, Summary, Timestamp, Success Rate", fontsize=10)

    # Refresh Button
    ax.add_patch(patches.Rectangle((440, 40), 120, 30, edgecolor="black", facecolor="#006699"))
    ax.text(455, 60, "Refresh", fontsize=10, color="white")

    # Save PNG
    image_path = "weather_dashboard_wireframe.png"
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()

    # Convert to PDF
    img = Image.open(image_path)
    img.save("weather_wireframe.pdf", "PDF", resolution=100.0)
    print("✅ Saved: weather_wireframe.pdf")

if __name__ == "__main__":
    draw_wireframe_layout()