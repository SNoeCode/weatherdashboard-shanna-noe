import tkinter as tk
from tkinter import messagebox
import random

class ClimateQuizGame:
    def __init__(self, parent_window):
        # Create popup window
        self.game_window = tk.Toplevel(parent_window)
        self.game_window.title("Climate Clues & City Views")
        self.game_window.geometry("700x500")
        self.game_window.configure(bg="#f8fafc")

        self.score = 0
        self.questions_asked = 0

        # Keep the window on top
        self.game_window.attributes('-topmost', True)
        self.game_window.focus_force()
        self.game_window.grab_set()
        self.keep_on_top_loop()

        # All weather datasets based on your CSV data
        self.weather_data = {
            'j_weather_data': [
                {'City': 'Perth Amboy', 'State': 'New Jersey', 'Country': 'US', 'Temperature': 80, 'Humidity': 62, 'Wind_Speed': 10},
                {'City': 'Kyoto', 'State': '', 'Country': 'JP', 'Temperature': 79, 'Humidity': 89, 'Wind_Speed': 1},
                {'City': 'Reethi Rah', 'State': 'Malé Atoll', 'Country': 'MV', 'Temperature': 82, 'Humidity': 74, 'Wind_Speed': 1},
                {'City': 'Río Piedras', 'State': 'Puerto Rico', 'Country': 'US', 'Temperature': 84, 'Humidity': 71, 'Wind_Speed': 15},
                {'City': 'Death Valley Junction', 'State': 'California', 'Country': 'US', 'Temperature': 68, 'Humidity': 28, 'Wind_Speed': 7},
                {'City': 'San Diego', 'State': 'California', 'Country': 'US', 'Temperature': 64, 'Humidity': 78, 'Wind_Speed': 3},
                {'City': 'Nome', 'State': 'Alaska', 'Country': 'US', 'Temperature': 46, 'Humidity': 93, 'Wind_Speed': 0},
                {'City': 'New York', 'State': 'New York', 'Country': 'US', 'Temperature': 82, 'Humidity': 53, 'Wind_Speed': 14},
                {'City': 'Los Angeles', 'State': 'California', 'Country': 'US', 'Temperature': 67, 'Humidity': 73, 'Wind_Speed': 8},
                {'City': 'Osaka', 'State': 'Osaka Prefecture', 'Country': 'JP', 'Temperature': 84, 'Humidity': 70, 'Wind_Speed': 3},
                {'City': 'Cincinnati', 'State': 'Ohio', 'Country': 'US', 'Temperature': 93, 'Humidity': 60, 'Wind_Speed': 8}
            ],
            's_weather_data': [
                {'City': 'Nashville', 'State': 'TN', 'Country': 'US', 'Temperature': 77.1, 'Humidity': 68, 'Wind_Speed': 9.22},
                {'City': 'Knoxville', 'State': 'TN', 'Country': 'US', 'Temperature': 74.6, 'Humidity': 79, 'Wind_Speed': 1.01},
                {'City': 'Salt Lake City', 'State': 'UT', 'Country': 'US', 'Temperature': 78.7, 'Humidity': 33, 'Wind_Speed': 4.61},
                {'City': 'Austin', 'State': 'TX', 'Country': 'US', 'Temperature': 88.8, 'Humidity': 67, 'Wind_Speed': 4.61},
                {'City': 'Tokyo', 'State': '', 'Country': 'JP', 'Temperature': 27.8, 'Humidity': 83, 'Wind_Speed': 4.63},
                {'City': 'St Louis', 'State': 'MO', 'Country': 'US', 'Temperature': 74.5, 'Humidity': 55, 'Wind_Speed': 8.05}
            ],
            'm_weather_data': [
                {'City': 'New York', 'State': 'NY', 'Country': 'USA', 'Temperature': 91.04, 'Humidity': 54, 'Wind_Speed': 7.7},
                {'City': 'New York', 'State': 'NY', 'Country': 'USA', 'Temperature': 93.65, 'Humidity': 36, 'Wind_Speed': 11.05},
                {'City': 'New York', 'State': 'NY', 'Country': 'USA', 'Temperature': 78.62, 'Humidity': 76, 'Wind_Speed': 18.54},
                {'City': 'London', 'State': '', 'Country': 'UK', 'Temperature': 70.21, 'Humidity': 49, 'Wind_Speed': 9.66},
                {'City': 'London', 'State': '', 'Country': 'UK', 'Temperature': 74.64, 'Humidity': 42, 'Wind_Speed': 6.91},
                {'City': 'Tokyo', 'State': '', 'Country': 'Japan', 'Temperature': 94.42, 'Humidity': 51, 'Wind_Speed': 15.32},
                {'City': 'Tokyo', 'State': '', 'Country': 'Japan', 'Temperature': 91.71, 'Humidity': 35, 'Wind_Speed': 15.19}
            ],
            'v_weather_data': [
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 89.0, 'Humidity': 48, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 87.0, 'Humidity': 55, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 85.0, 'Humidity': 70, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 82.0, 'Humidity': 53, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 84.0, 'Humidity': 48, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 74.0, 'Humidity': 85, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 71.0, 'Humidity': 53, 'Wind_Speed': None},
                {'City': 'Atlanta', 'State': 'GA', 'Country': 'USA', 'Temperature': 83.0, 'Humidity': 81, 'Wind_Speed': None}
            ],
            't_weather_data': [
                {'City': 'New York', 'State': 'New York', 'Country': 'US', 'Temperature': 72, 'Humidity': 87, 'Wind_Speed': 26.46},
                {'City': 'New York', 'State': 'New York', 'Country': 'US', 'Temperature': 71, 'Humidity': 86, 'Wind_Speed': 20.71},
                {'City': 'New York', 'State': 'New York', 'Country': 'US', 'Temperature': 70, 'Humidity': 85, 'Wind_Speed': 24},
                {'City': 'New York', 'State': 'New York', 'Country': 'US', 'Temperature': 68, 'Humidity': 89, 'Wind_Speed': 17.27},
                {'City': 'New York', 'State': 'New York', 'Country': 'US', 'Temperature': 64, 'Humidity': 87, 'Wind_Speed': 15.99}
            ]
        }
        
        self.setup_ui()
        self.new_question()

    def keep_on_top_loop(self):
        if self.game_window.winfo_exists():
            self.game_window.lift()
            self.game_window.after(1000, self.keep_on_top_loop)
        
    def setup_ui(self):
        # Banner
        banner = tk.Label(self.game_window, text="🌤️ Climate Clues & City Views 🏙️", 
                         font=("Segoe UI", 18, "bold"), bg="#2563eb", fg="white", pady=10)
        banner.pack(fill="x")
        
        # Score
        self.score_label = tk.Label(self.game_window, text=f"Score: {self.score}/5", 
                                   font=("Segoe UI", 14), bg="#f8fafc")
        self.score_label.pack(pady=10)
        
        # Question area
        self.question_frame = tk.Frame(self.game_window, bg="#f8fafc")
        self.question_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Buttons frame
        self.buttons_frame = tk.Frame(self.game_window, bg="#f8fafc")
        self.buttons_frame.pack(pady=10)
        
        # Control buttons
        control_frame = tk.Frame(self.game_window, bg="#f8fafc")
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="New Question", command=self.new_question,
                 bg="#2563eb", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=5)
        tk.Button(control_frame, text="Close Game", command=self.game_window.destroy,
                 bg="#dc2626", fg="white", font=("Segoe UI", 10)).pack(side="left", padx=5)
    
    def get_random_data(self):        
        dataset_names = list(self.weather_data.keys())
        selected_datasets = random.sample(dataset_names, 2)
        
        samples = []
        self.selected_dataset_names = selected_datasets
        
        for dataset_name in selected_datasets:
            dataset = self.weather_data[dataset_name]          
            random_entry = random.choice(dataset)
            random_entry['dataset'] = dataset_name
            samples.append(random_entry)
        
        return samples
    
    def new_question(self):
        if self.questions_asked >= 5:
            self.end_game()
            return            
    
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()        
       
        self.samples = self.get_random_data()
        self.correct_answer = random.choice(self.samples)  
        
        question_data = self.generate_question()
        self.current_question = question_data
     
        tk.Label(self.question_frame, text=question_data['question'], 
                font=("Segoe UI", 12, "bold"), bg="#f8fafc", wraplength=600).pack(pady=10)
            
        clue_data = self.correct_answer
        clue_text = f"🌡️ Temperature: {clue_data['Temperature']}°F\n"
        clue_text += f"💧 Humidity: {clue_data['Humidity']}%"
        if clue_data.get('Wind_Speed') is not None:
            clue_text += f"\n💨 Wind Speed: {clue_data['Wind_Speed']} mph"
        
        tk.Label(self.question_frame, text=clue_text, 
                font=("Segoe UI", 11), bg="#f8fafc", justify="left").pack(pady=10)
        
        choices = question_data['choices']
        random.shuffle(choices)
        
        for choice in choices:
            btn = tk.Button(self.buttons_frame, text=choice, 
                          command=lambda c=choice: self.check_answer(c),
                          width=30, pady=5, font=("Segoe UI", 10))
            btn.pack(pady=2)
        
        self.questions_asked += 1
    
    def generate_question(self):        
        correct = self.correct_answer
        other_sample = [s for s in self.samples if s != correct][0]
      
        if correct['State']:
            correct_city = f"{correct['City']}, {correct['State']}"
        else:
            correct_city = f"{correct['City']}, {correct['Country']}"
                
        if other_sample['State']:
            wrong_city = f"{other_sample['City']}, {other_sample['State']}"
        else:
            wrong_city = f"{other_sample['City']}, {other_sample['Country']}"        
        
        all_wrong_answers = []
        for dataset_name, dataset in self.weather_data.items():
            if dataset_name not in self.selected_dataset_names:           
                random_entry = random.choice(dataset)
                if random_entry['State']:
                    wrong_answer = f"{random_entry['City']}, {random_entry['State']}"
                else:
                    wrong_answer = f"{random_entry['City']}, {random_entry['Country']}"
                all_wrong_answers.append(wrong_answer)
             
        additional_wrongs = random.sample(all_wrong_answers, min(2, len(all_wrong_answers)))
        
        # Create choices list
        choices = [correct_city, wrong_city] + additional_wrongs
        
        # Generate question 
        temp = correct['Temperature']
        humidity = correct['Humidity']
        wind_speed = correct.get('Wind_Speed')
        
        question_text = self.create_question_text(temp, humidity, wind_speed)
        
        return {
            'question': question_text,
            'choices': choices,
            'correct': correct_city
        }
    
    def create_question_text(self, temp, humidity, wind_speed):       
        questions = []
        
        # Temperature-based questions
        if temp > 85:
            questions.append("This hot weather is most likely from which city?")
            questions.append("Which city is experiencing this warm climate?")
        elif temp < 50:
            questions.append("This cool weather is most likely from which northern city?")
            questions.append("Which city is experiencing this cold climate?")
        elif temp >= 70 and temp <= 85:
            questions.append("This moderate temperature is typical of which city?")
            questions.append("Which city has this pleasant weather?")
        else:
            questions.append("Which city matches this temperature reading?")
        
        # Humidity-based questions
        if humidity > 80:
            questions.append("This very humid weather is characteristic of which coastal or tropical city?")
        elif humidity < 40:
            questions.append("This dry climate is typical of which desert or mountain city?")
        
        # Wind-based questions
        if wind_speed is not None and wind_speed > 15:
            questions.append("This windy weather is characteristic of which city?")
        elif wind_speed is not None and wind_speed < 2:
            questions.append("This calm weather with little wind is typical of which city?")
        
        # Combined weather questions
        if temp > 80 and humidity > 70:
            questions.append("This hot and humid weather is typical of which city?")
        elif temp < 70 and humidity > 80:
            questions.append("This cool and very humid weather is characteristic of which city?")
        elif temp > 75 and humidity < 40:
            questions.append("This warm and dry weather is typical of which city?")
        
        # Default question
        if not questions:
            questions.append("Based on this weather data, which city is it?")
        
        return random.choice(questions)
    
    def check_answer(self, selected):
        if selected == self.current_question['correct']:
            self.score += 1
            feedback_msg = f"✅ Correct!\nScore: {self.score}/5"
            title = "Correct! 🎉"
        else:
            correct = self.current_question['correct']
            feedback_msg = f"❌ Close! The correct answer was: {correct}\nScore: {self.score}/5"
            title = "Oops!"

        self.score_label.config(text=f"Score: {self.score}/5")
        self.show_feedback_popup(title, feedback_msg)
       
        self.game_window.after(1500, self.new_question)
    
    def show_feedback_popup(self, title, message):
        popup = tk.Toplevel(self.game_window)
        popup.title(title)
        popup.geometry("300x150")
        popup.configure(bg="#e0f2fe")
        popup.transient(self.game_window)
        popup.grab_set()
        popup.attributes('-topmost', True)

        tk.Label(popup, text=message, font=("Segoe UI", 12), bg="#e0f2fe", wraplength=280).pack(pady=20)
        tk.Button(popup, text="Next", command=popup.destroy, bg="#16a34a", fg="white").pack(pady=10)
    
    def end_game(self):
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Final score
        percentage = (self.score / 5) * 100
        if percentage >= 80:
            emoji = "🏆"
            message = "Climate Expert!"
        elif percentage >= 60:
            emoji = "🌟"
            message = "Weather Detective!"
        else:
            emoji = "🌤️"
            message = "Geography Explorer!"
        
        tk.Label(self.question_frame, text=f"{emoji} Game Complete! {emoji}", 
                font=("Segoe UI", 16, "bold"), bg="#f8fafc").pack(pady=20)
        tk.Label(self.question_frame, text=f"Final Score: {self.score}/5 ({percentage:.0f}%)", 
                font=("Segoe UI", 14), bg="#f8fafc").pack(pady=10)
        tk.Label(self.question_frame, text=message, 
                font=("Segoe UI", 12), bg="#f8fafc").pack(pady=5)
    
        # Show which datasets were used
        datasets_used = ", ".join(self.selected_dataset_names)
        tk.Label(self.question_frame, text=f"Data from: {datasets_used}", 
                font=("Segoe UI", 10), bg="#f8fafc", fg="#6b7280").pack(pady=5)
        
        # Play again button
        tk.Button(self.buttons_frame, text="Play Again", 
                 command=self.restart_game, bg="#16a34a", fg="white",
                 font=("Segoe UI", 12)).pack(pady=10)
    
    def restart_game(self):
        self.score = 0
        self.questions_asked = 0
        self.score_label.config(text=f"Score: {self.score}/5")
    
        # Reinstate focus 
        self.game_window.lift()
        self.game_window.focus_force()
        self.game_window.attributes('-topmost', True)
        self.game_window.grab_set()

        self.new_question()

# Integration function for your main weather app
def launch_climate_quiz(parent_window):
    """Call this function from your main weather app"""
    ClimateQuizGame(parent_window)
