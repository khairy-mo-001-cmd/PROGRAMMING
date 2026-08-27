import tkinter as tk
from tkinter import messagebox

# 1. الـ Class بتاعنا (الموديل)
class Task:
    def __init__(self, title, description):
        self.title = title
        self.description = description

    def show_info(self):
        return f"المهمة: {self.title} | التفاصيل: {self.description}"


# 2. النافذة الرئيسية للبرنامج
root = tk.Tk()
root.title("ملاحظات والمهام - Tkinter")
root.geometry("400x300")

# قائمة لتخزين الأوبجيكتس اللي هيتم إنشاؤها
tasks_list = []


# 3. دالة إنشاء النافذة الفرعية (Modal/Dialog) عند الضغط على الزرار
def open_add_task_dialog():
    # إنشاء نافذة فرعية جديدة فوق النافذة الرئيسية
    dialog = tk.Toplevel(root)
    dialog.title("إضافة مهمة جديدة")
    dialog.geometry("300x250")
    dialog.grab_set()  # بتمنع التفاعل مع النافذة الرئيسية لحد ما تقفل دي

    # --- خانة العنوان ---
    tk.Label(dialog, text=":اسم المهمة").pack(pady=(10, 2))
    title_entry = tk.Entry(dialog, width=30)
    title_entry.pack(pady=2)

    # --- خانة الوصف/التفاصيل ---
    tk.Label(dialog, text=":التفاصيل").pack(pady=(10, 2))
    desc_entry = tk.Entry(dialog, width=30)
    desc_entry.pack(pady=2)

    # --- دالة الحفظ وإنشاء الأوبجيكت ---
    def save_task():
        title = title_entry.get().strip()
        desc = desc_entry.get().strip()

        if title:  # التأكد إن العنوان مش فاضي
            # إنشاء أوبجيكت جديد من الـ Class
            new_task = Task(title, desc)
            tasks_list.append(new_task)

            # طباعة للتأكد من إن الأوبجيكت اتعمل بنجاح
            print("تم إنشاء الأوبجيكت بنجاح:")
            print(new_task.show_info())

            messagebox.showinfo("نجاح", f"تمت إضافة: {new_task.title}")
            dialog.destroy()  # إغلاق النافذة الفرعية
        else:
            messagebox.showwarning("تنبيه", "يرجى كتابة اسم المهمة أولاً")

    # --- زرار الحفظ جوة النافذة الفرعية ---
    save_btn = tk.Button(dialog, text="حفظ المهمة", command=save_task, bg="#4CAF50", fg="white")
    save_btn.pack(pady=20)


# 4. الزرار الرئيسي في الشاشة الأساسية
add_button = tk.Button(
    root, 
    text="+ إضافة مهمة جديدة", 
    command=open_add_task_dialog,
    font=("Arial", 12, "bold"),
    bg="#2196F3",
    fg="white",
    padx=10,
    pady=5
)
add_button.pack(pady=100)

# تشغيل النافذة
root.mainloop()