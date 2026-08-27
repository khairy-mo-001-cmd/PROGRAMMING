import datetime as dt

tasks_number = 0
ongoing_tasks_number = 0
canseld_taskes = 0

class Task:
    def __init__(
        self,
        task_name,
        task_number,
        task_priority,
        task_duration,
        task_deadline=None,
        task_date=None,
        task_status="ongoing"
    ):
        if task_date is None:
            task_date = dt.datetime.now()
        
        if task_deadline is None:
            task_deadline = dt.datetime.now() + dt.timedelta(days=1)

        self.task_name = task_name
        self.task_number = task_number
        self.task_priority = task_priority
        self.task_duration = task_duration
        self.task_deadline = task_deadline
        self.task_date = task_date
        self.task_status = task_status

    def __repr__(self):
        return f"<Task {self.task_number}: {self.task_name}>"


class TaskManager:
    def __init__(self):
        self.tasks = []
        self.ongoing_tasks = []
        self.finished_tasks = []

    def create_task(
        self,
        task_name="task",
        task_number=None,  # 👈 بنخلي القيمة الافتراضية None
        task_priority=None,
        task_duration=None,
        task_deadline=None
    ):
        global tasks_number
        global ongoing_tasks_number

        # 👈 بنحسب الرقم لحظة تشغيل الدالة
        if task_number is None:
            task_number = tasks_number + 1

        task = Task(
            task_name,
            task_number,
            task_priority,
            task_duration,
            task_deadline
        )

        self.tasks.append(task)
        self.ongoing_tasks.append(task)

        tasks_number += 1
        ongoing_tasks_number += 1
                
        print("task have been succesfully added")
        print(task.task_name, task.task_number)    
        return task

    def end_task(self, task):
        if task == None :
           pass
        global ongoing_tasks_number
        task.task_status = "finished"

        self.ongoing_tasks.remove(task)
        self.finished_tasks.append(task)
        ongoing_tasks_number -= 1

    def history (self):
        if tasks_number == 0 :
            print("there is no tasks history")
        else:
            print(self.tasks)    