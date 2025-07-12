# 🌟 Week 13 Reflection

| Field                  | Your Entry                              |
|------------------------|------------------------------------------|
| Name                   | Shanna Noe                               |
| GitHub Username        | SNoeCode                                 |
| Preferred Track        | Data / Visual / Interactive / Smart      |
| Team Interest          | Yes — Contributor                        |

---

## 📌 Key Milestones Reached

- Fully implemented **weather icon system** with Pillow and fallback logic
- Created `icon_map` for condition-based image rendering
- Integrated dynamic icons into both current weather and forecast views
- Built foundational GUI structure with Home and Favorites tabs
- Refactored fonts and layout for cleaner appearance

---


## 🧠 What I Learned

- Weather icons dramatically improve the clarity and user-friendliness of the interface
- Pillow allows powerful image resizing and embedding for GUI components
- Handling edge cases (e.g., unknown weather conditions) requires default logic
- Refactoring fonts and layouts helps avoid cross-platform glitches

---


## 🔍 Skill Assessment

| Skill Area             | Confidence Level | Notes                                                  |
|------------------------|------------------|--------------------------------------------------------|
| Icon Integration       | ⭐⭐⭐⭐            | Resizing, fallback handling, and GUI embedding working |
| File Handling          | ⭐⭐⭐             | Gaining confidence with managing assets and paths      |
| Tkinter Layout         | ⭐⭐              | Still learning positioning and padding                 |
| Feature Planning       | ⭐⭐⭐             | Clear vision for next steps and modular expansion      |

---
🧱 Biggest Challenges

- Building a responsive and visually consistent Tkinter UI layout using .pack() and .grid()
- Finding consistent icon styles for all weather types and handling fallbacks cleanly
- Resolving Pylance .image attribute warning on Label widgets in icon rendering
- Adjusting layout spacing when forecast blocks and icons are added to the weather frame
- Avoiding layout shifts and flicker when weather data refreshes multiple times



---

## 🌈 Favorite Feature Added

| Feature Name     | Why It Stands Out                                      |
|------------------|--------------------------------------------------------|
| Weather Icons    | Adds instant visual feedback and elevates the UI       |

---


## 📊 Data + Demo Tracking

| File Name               | Format | Example Entry                                         |
|-------------------------|--------|--------------------------------------------------------|
| weather_history.csv     | CSV    | 2025-07-10,Tokyo,30.2,Sunny                           |
| prediction_log.json     | JSON   | {"date": "2025-07-11", "guess": 86.2, "actual": 85.1} |
| mascot_mood_log.txt     | TXT    | 2025-07-10,Rainy,Gloomy                               |

---
## 🔜 Next Steps

- Begin implementing the **Simple Statistics** module
- Build out Favorites tab backend and summary rendering
- Introduce `Tomorrow’s Guess` prediction logic
- Connect mascot feature to weather conditions
- Add export-to-CSV functionality

---

## 🧭 Risk Table

| Risk                  | Likelihood | Impact | Mitigation Plan                                       |
|-----------------------|------------|--------|-------------------------------------------------------|
| Icon mismatch         | Low        | Medium | Use default icon fallback                            |
| UI spacing issues     | Medium     | Low    | Continue testing `.pack()` and `.grid()` combinations |
| Forecast data parsing | Medium     | Medium | Add error handling for missing entries                |


