import datetime as dt
class habits: 
    def __init__(self ,habit_name ,habit_number , habit_periority , habit_duration , habit_deadline=None, habit_date=None):
        if habit_date is None:
            habit_date = dt.datetime.now()
        if habit_deadline is None:
            habit_deadline = dt.datetime.now() + dt.timedelta(days=30)

        self.habit_name = habit_name
        self.habit_number = habit_number
        self.habit_periority = habit_periority
        self.habit_duration = habit_duration
        self.habit_deadline = habit_deadline
        self.habit_date = habit_date

       
class habits_manager:
    
    def __init__(self):
        self.habits = []
        self.ongoing_habits = []
        self.finished_habits = []

    def create_habit(self, habit_name, habit_number, habit_periority, habit_duration, habit_deadline=None):
        habit = habits(habit_name, habit_number, habit_periority, habit_duration, habit_deadline)
        self.habits.append(habit)
        self.ongoing_habits.append(habit)
        return habit

    def end_habit(self, habit):
        if habit in self.ongoing_habits:
            self.ongoing_habits.remove(habit)
            self.finished_habits.append(habit)

            
    def save_habit(self, habit):
        # Save the habit to a file or database
        pass

