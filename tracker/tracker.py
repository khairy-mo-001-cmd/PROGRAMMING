import tkinter as tk
import task as tas 
import habits as hab 
import json as js
import datetime as dt
import sqlite3 as sql
#=======================================
#the code 
#=======================================
task_manager = tas.TaskManager()
habit_manager = hab.habits_manager()
window = tk.Tk()
window.title("Task and Habit Tracker")
window.geometry("800x600")
new_task_button = tk.Button(window, text="add new task",command=task_manager.create_task)
new_task_button.pack()
end_task_button = tk.Button(window ,text="fenish the task",command= task_manager.end_task)
end_task_button.pack()
hestory_button = tk.Button(window ,text="show the tasks history " ,command=task_manager.history)
hestory_button.pack()
window.mainloop()