Field	                            Your Entry
Name                                Shanna Noe
Github Username                     SNoeCode                
Preferred Feature Track	            Data / Visual / Interactive / Smart
Team Interest	Yes / No            Yes — Contributor

Key Takeaways: What did you learn about capstone goals and expectations?
The capstone isn't just “build something cool”—it’s about planning with intent, 
breaking work into modular parts, and making sure each piece actually works well 
with the others. Clean code, creative thinking, and feature polish all matter. 
Having a unique hook (like a mascot) isn’t just fluff—it’s what makes the project yours.


Concept Connections: Which Week 1–10 skills feel strongest? Which need more practice?
I am confident with file handling, parsing CSV/JSON/TXT format
I am  Comfortable building modular Python functions and keeping logic tidy

I need more practice with
Tkinter, matploylib, and pandas

Early Challenges: Any blockers (e.g., API keys, folder setup)?
Figuring out the best  High-Level Architecture Sketch

Support Strategies: Which office hours or resources can help you move forward?
Slack is a great resource i use if i have any problems 



| # | Feature Name         | Difficulty | Why You Chose It                                       |
|---|----------------------|------------|--------------------------------------------------------|
| 1 | Simple Statistics    | ⭐         | Reinforces skills in file handling and data parsing    |
| 2 | Weather Icons        | ⭐⭐      | Adds visual polish and a more engaging user interface   |
| 3 | Tomorrow’s Guess     | ⭐⭐⭐    | Challenges me to apply logic and analyze patterns      |
| 4 | Enhancement: Mascot  | ✨         | Gives the app personality and makes it more memorable  |


                 ┌────────────────────┐
                 │  APIService        │
                 │────────────────────│
                 │ + getWeatherData() │───────┐
                 └────────────────────┘       │
                                              ▼
     ┌────────────────────┐        ┌─────────────────────────┐
     │ WeatherController  │◄──────▶│   WeatherModel          │
     │────────────────────│        │─────────────────────────│
     │ + updateView()     │        │ + parseData()           │
     │ + handlePrediction │        │ + predictTomorrow()     │
     └────────────────────┘        └─────────────────────────┘
              │                               │
              ▼                               ▼
     ┌────────────────────┐        ┌─────────────────────────┐
     │  WeatherView (Tk)  │        │ RecommendationEngine    │
     │────────────────────│        │─────────────────────────│
     │ + renderStats()    │        │ + analyzePatterns()     │
     │ + showIcons()      │        │ + logPrediction()       │
     └────────────────────┘        └─────────────────────────┘
               ▲
               │
     ┌────────────────────┐
     │ MascotModule       │
     │────────────────────│
     │ + respondToWeather │
     │ + moodLogging()    │
     └────────────────────┘


| File/Table Name       | Format | Example Row                                |
|------------------------|--------|---------------------------------------------|
| weather_history.csv    | csv    | 2025-06-30,Knoxville,78,Clear                |
| mascot_mood_log.txt    | txt    | 2025-06-30,Sunny,Happy                      |
| prediction_log.json    | json   | {"date": "2025-07-01", "guess": 85, "actual": 82} |

Week  | Monday                | Tuesday              | Wednesday             | Thursday              | Friday                | Key Milestone
---------------------------------------------------------------------------------------------------------------
11    | Project introduction  | System Architecture  | Data Modeling         | Project Planning      | Test planing          | Setting up 

12    | Data Collection       | Data Processing      | Basic Ui              | Buffer / catch-up     | Test full flow        | Data Planning

13    | Data Visualization    | Location Services    | Historial Analysis    | SkillsCheck #5        | Feature Integration   | Feature 1 complete

14    | Start Feature 2       | Polish UI            | Setup Team Folders    | Finalize feature      | Export WeatherData    | Feature 2 complete

15    | Start Feature 3       | Refactor             | Organize              | Start Assigned Team   | Collaborate            | All features complete

16    | Add mascot enhancement| Write documentation  | Add unit tests        | Final packaging       | Screenshots + finalize| Ready-to-ship app

17    | Rehearse demo         | Address feedback     | Present individual app| Present team feature  | Celebrate! 🎉         | Demo Day



| Risk               | Likelihood | Impact | Mitigation Plan                                      |
|--------------------|------------|--------|------------------------------------------------------|
| API Rate Limit     | Medium     | Medium | Use caching, add delays between calls                |
| Canvas UI Glitches | Medium     | Low    | Test visuals often and simplify icon rendering       |
| Prediction Accuracy| High       | Low    | Make it optional/fun and label predictions clearly   |