# 🖼️ Weather Dashboard — Figma Wireframe Specs

## 🎨 Canvas & Typography

- Canvas Size: `1000px × 700px`
- Base Font: `Segoe UI`, fallback `sans-serif`
- Font Sizes:
  - Title: `18pt`
  - Labels: `12pt`
  - Input Fields: `12pt`
  - Weather Cards: `10pt–12pt`
- Font Weight Usage:
  - Normal text: `Regular`
  - Headers & Buttons: `Bold`
- Background Colors:
  - Root Window: `#f7fbff`
  - Forecast Cards: `#e6f7ff`
  - Favorites Summary Box: `#e6f7ff`
- Accent Colors:
  - Button Fill: `#006699`
  - Button Hover: `#004466`
  - Label Text: `#333333`
  - Header Titles: `#0059b3`
  - Error/Warning: `#cc3300`

---

## 🏠 Home Tab

### 🔎 Search Bar

| Element         | Size                 | Notes                       |
| --------------- | -------------------- | --------------------------- |
| City Entry      | `Width: 180px`       | Pre-filled with “Knoxville” |
| Country Entry   | `Width: 100px`       | Pre-filled with “US”        |
| Search Button   | `120×40 px`          | Styled with bold + blue     |
| Forecast Toggle | `Radio Button Group` | “🌤️ Now” only (active)      |

### 🌤️ Weather Display Box (`weather_frame`)

- Container: `LabelFrame`, width `90%`, padding `10px`, title `"Current Weather"`
- Forecast toggle placement: `Row 3`, under inputs
- Actions:
  - Button: `"⭐ Save to Favorites"` — Centered, `Full Row`, height `40px`
  - Button: `"💾 Save All to CSV"` — Centered, `Full Row`, height `40px`

### 🌡️ Weather Result Elements

| Element           | Size           | Styling                     |
| ----------------- | -------------- | --------------------------- |
| Icon              | `64×64 px`     | Centered, fade-in           |
| Temperature Label | `24pt Bold`    | Fade-in text, gray to black |
| Description       | `12pt Regular` | Fade-in, e.g. `Cloudy`      |

---

## 📆 Forecast Cards (Rendered in `forecast_frame`)

- Container: Horizontal `LabelFrame`, title `"5-Day Forecast"`, padding `10px`
- Card Dimensions: `140px wide`, height auto
- Card Count: Max `5 cards`, each spaced `12px` apart

| Card Element      | Size        |
| ----------------- | ----------- |
| Icon              | `48×48 px`  |
| Date              | `10pt Bold` |
| Temp (converted)  | `10pt`      |
| Condition Summary | `10pt`      |

---

## 🌍 Favorites Tab

### 🧭 Dashboard Panel

| Element             | Spec                                                   |
| ------------------- | ------------------------------------------------------ |
| Title               | `Text 18pt bold` — `"🌍 Favorite Cities Dashboard"`    |
| Summary Display Box | `Text Widget: 80×20` — bg: `#e6f7ff`, fg: `#000066`    |
| Scrollable content  | Grouped blocks per city, styled with `Text.tag_config` |

### 🔄 Refresh Button

- Location: Center-bottom of tab
- Size: `Width 120px`, Height `40px`
- Label: `"🔄 Refresh"`

---

## 📁 Asset Specs

### 📦 Icons

| Weather Type | Image Path                                                | Render Size       |
| ------------ | --------------------------------------------------------- | ----------------- |
| Clear        | `icons/icons8-sun-50.png`                                 | `64x64` / `48x48` |
| Rain         | `icons/icons8-rain-50.png`                                | Same              |
| Thunderstorm | `icons/icons8-thunderstorm-100.png`                       | Resized           |
| Clouds       | `icons/icons8-clouds-50.png`                              | Same              |
| Snow         | `icons/icons8-snow-50.png`                                | Same              |
| Wind         | `icons/icons8-windy-weather-50.png`                       | Same              |
| Mist         | `icons/weather_icons_dovora_interactive/PNG/128/mist.png` | Same              |
| Fallback     | `icons/icons8-question-mark-50.png`                       | Same              |

---

## 🧠 UI Logic Summary (Optional Annotations for Figma)

- All weather cards fade in on data refresh
- Icons change dynamically based on API `weather_summary`
- Temperature converted based on `country == "US"`
- Each favorite displays:
  - Latest temp, summary, humidity, wind, pressure
  - Timestamp
  - API success rate over 24 hours

---
