# app_ui.py
import customtkinter as ctk
import threading
import asyncio
import queue
import database
import config
from orchestrator import Orchestrator
from datetime import datetime, timedelta
import platform

# FIXED: Added the missing conditional import for windows_toasts
WINDOWS_TOASTS_AVAILABLE = False
if platform.system() == "Windows":
    try:
        from windows_toasts import WindowsToaster, Toast
        WINDOWS_TOASTS_AVAILABLE = True
    except ImportError:
        print("Could not import windows-toasts. Windows notifications disabled.")

class SettingsWindow(ctk.CTkToplevel):
    # ... (No changes in this class) ...
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Settings")
        self.geometry("550x300")
        self.transient(self.master)
        self.grid_columnconfigure(1, weight=1)
        self.app_state = config.read_state()
        current_start_hr, current_start_min = self.app_state.get("quiet_hours_start", "22:00").split(':')
        current_end_hr, current_end_min = self.app_state.get("quiet_hours_end", "08:00").split(':')
        self.hour_options = [f"{h:02d}" for h in range(24)]
        self.minute_options = [f"{m:02d}" for m in range(60)]
        self.api_label = ctk.CTkLabel(self, text="Pushover API Token:")
        self.api_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.api_entry = ctk.CTkEntry(self, width=300, placeholder_text="••••••••••••••••••••••" if config.get_secret(config.PUSHOVER_API_SERVICE, "api_token") else "Enter New API Token")
        self.api_entry.grid(row=0, column=1, columnspan=2, padx=20, pady=10, sticky="ew")
        self.user_label = ctk.CTkLabel(self, text="Pushover User Key:")
        self.user_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.user_entry = ctk.CTkEntry(self, width=300, placeholder_text="••••••••••••••••••••••" if config.get_secret(config.PUSHOVER_USER_SERVICE, "user_key") else "Enter New User Key")
        self.user_entry.grid(row=1, column=1, columnspan=2, padx=20, pady=10, sticky="ew")
        self.quiet_start_label = ctk.CTkLabel(self, text="Quiet Hours Start:")
        self.quiet_start_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.quiet_start_hour_combo = ctk.CTkComboBox(self, values=self.hour_options, width=80)
        self.quiet_start_hour_combo.grid(row=2, column=1, padx=(20, 5), pady=10, sticky="w")
        self.quiet_start_hour_combo.set(current_start_hr)
        self.quiet_start_min_combo = ctk.CTkComboBox(self, values=self.minute_options, width=80)
        self.quiet_start_min_combo.grid(row=2, column=2, padx=(0, 20), pady=10, sticky="w")
        self.quiet_start_min_combo.set(current_start_min)
        self.quiet_end_label = ctk.CTkLabel(self, text="Quiet Hours End:")
        self.quiet_end_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.quiet_end_hour_combo = ctk.CTkComboBox(self, values=self.hour_options, width=80)
        self.quiet_end_hour_combo.grid(row=3, column=1, padx=(20, 5), pady=10, sticky="w")
        self.quiet_end_hour_combo.set(current_end_hr)
        self.quiet_end_min_combo = ctk.CTkComboBox(self, values=self.minute_options, width=80)
        self.quiet_end_min_combo.grid(row=3, column=2, padx=(0, 20), pady=10, sticky="w")
        self.quiet_end_min_combo.set(current_end_min)
        self.save_button = ctk.CTkButton(self, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=4, column=0, columnspan=3, padx=20, pady=20)
    def save_settings(self):
        new_api_token, new_user_key = self.api_entry.get(), self.user_entry.get()
        secrets_saved = False
        if new_api_token: config.set_secret(config.PUSHOVER_API_SERVICE, "api_token", new_api_token); secrets_saved = True
        if new_user_key: config.set_secret(config.PUSHOVER_USER_SERVICE, "user_key", new_user_key); secrets_saved = True
        self.app_state["quiet_hours_start"] = f"{self.quiet_start_hour_combo.get()}:{self.quiet_start_min_combo.get()}"
        self.app_state["quiet_hours_end"] = f"{self.quiet_end_hour_combo.get()}:{self.quiet_end_min_combo.get()}"
        config.save_state(self.app_state)
        if secrets_saved: self.master.log("✅ Secrets and settings saved.")
        else: self.master.log("✅ Settings saved.")
        self.destroy()

class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Mind Set - Task Scheduler")
        self.geometry("800x700")
        database.init_db()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.task_widgets = {}
        self.update_queue = queue.Queue()
        self.orchestrator = Orchestrator(self.update_queue)
        self.orchestrator_thread = threading.Thread(target=self.run_orchestrator_in_thread, daemon=True)
        self.orchestrator_thread.start()
        self.after(100, self.process_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.task_list_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Scheduled Tasks")
        self.task_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.task_list_frame.grid_columnconfigure(0, weight=1)
        self.add_task_form = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.add_task_form.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.add_task_form.grid_columnconfigure(0, weight=1)
        self.task_type_var = ctk.StringVar(value="One-Time")
        self.task_type_segmented_button = ctk.CTkSegmentedButton(
            self.add_task_form, values=["One-Time", "Recurring"],
            command=self.toggle_task_type_fields, variable=self.task_type_var
        )
        self.task_type_segmented_button.grid(row=0, column=0, columnspan=4, padx=5, pady=(5,10), sticky="ew")
        self.dynamic_fields_frame = ctk.CTkFrame(self.add_task_form, fg_color="transparent")
        self.dynamic_fields_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.desc_entry = ctk.CTkEntry(self.dynamic_fields_frame, placeholder_text="Description (leave blank for random quote)")
        self.date_entry = ctk.CTkEntry(self.dynamic_fields_frame, placeholder_text="Date (MM/DD/YYYY)")
        self.time_entry = ctk.CTkEntry(self.dynamic_fields_frame, placeholder_text="Time (HH:MM)")
        self.recurrence_options = ["Every Minute", "Every 5 Minutes", "Hourly", "Daily", "Weekly", "Monthly", "Yearly"]
        self.recurrence_dropdown = ctk.CTkComboBox(self.dynamic_fields_frame, values=self.recurrence_options, command=self.toggle_task_type_fields)
        self.day_of_week_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.day_of_week_dropdown = ctk.CTkComboBox(self.dynamic_fields_frame, values=self.day_of_week_options)
        self.day_of_month_entry = ctk.CTkEntry(self.dynamic_fields_frame, placeholder_text="Day of Month (1-31)")
        self.add_button = ctk.CTkButton(self.add_task_form, text="Schedule Task", command=self.add_task)
        self.add_button.grid(row=2, column=0, columnspan=4, padx=5, pady=(10,0))
        self.date_entry.bind("<FocusIn>", self.on_date_focus)
        self.time_entry.bind("<FocusIn>", self.on_time_focus)
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Starting up...", anchor="w")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.settings_button = ctk.CTkButton(self.bottom_frame, text="Settings", width=100, command=self.open_settings)
        self.settings_button.grid(row=0, column=1, padx=10, pady=5)
        self.toggle_task_type_fields("One-Time")
        self.refresh_task_list()

    def run_orchestrator_in_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.orchestrator.start()
        loop.run_forever()

    def toggle_task_type_fields(self, _=None):
        for widget in [self.desc_entry, self.date_entry, self.time_entry, self.recurrence_dropdown, self.day_of_week_dropdown, self.day_of_month_entry]:
            widget.grid_remove()
        main_task_type = self.task_type_var.get()
        if main_task_type == "One-Time":
            self.desc_entry.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            self.date_entry.grid(row=1, column=0, padx=5, pady=5)
            self.time_entry.grid(row=1, column=1, padx=5, pady=5)
        elif main_task_type == "Recurring":
            self.desc_entry.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            self.recurrence_dropdown.grid(row=1, column=0, padx=5, pady=5)
            recurrence_type = self.recurrence_dropdown.get()
            if recurrence_type in ["Daily", "Weekly", "Monthly", "Yearly"]:
                self.time_entry.grid(row=1, column=1, padx=5, pady=5)
            if recurrence_type == "Weekly":
                self.day_of_week_dropdown.grid(row=1, column=2, padx=5, pady=5)
            if recurrence_type == "Monthly":
                self.day_of_month_entry.grid(row=1, column=2, padx=5, pady=5)
            if recurrence_type == "Yearly":
                self.date_entry.grid(row=1, column=2, padx=5, pady=5)

    def add_task(self):
        task_type, task_data = self.task_type_var.get(), {}
        try:
            task_data["description"] = self.desc_entry.get()
            if task_type == "One-Time":
                dt_str = f"{self.date_entry.get()} {self.time_entry.get()}"
                task_data.update({"task_type": "one_time", "run_datetime": datetime.strptime(dt_str, '%m/%d/%Y %H:%M')})
            elif task_type == "Recurring":
                rule = self.recurrence_dropdown.get()
                task_data.update({"task_type": "recurring", "recurrence_rule": rule})
                if rule == "Every Minute": task_data.update({"recurrence_minute": "*/1"})
                elif rule == "Every 5 Minutes": task_data.update({"recurrence_minute": "*/5"})
                elif rule == "Hourly": task_data.update({"recurrence_minute": "0"})
                else:
                    t = datetime.strptime(self.time_entry.get(), '%H:%M')
                    task_data.update({"recurrence_hour": str(t.hour), "recurrence_minute": str(t.minute)})
                    if rule == "Weekly": task_data.update({"recurrence_day_of_week": self.day_of_week_dropdown.get()[:3].lower()})
                    elif rule == "Monthly": task_data.update({"recurrence_day_of_month": self.day_of_month_entry.get()})
                    elif rule == "Yearly":
                        d = datetime.strptime(self.date_entry.get(), '%m/%d/%Y')
                        task_data.update({"recurrence_month": str(d.month), "recurrence_day_of_month": str(d.day)})
        except ValueError:
            self.log("❌ Invalid or missing fields for the selected task type."); return
        task_id = database.create_task(task_data)
        if task_id:
            self.log(f"✅ Task {task_id} created.")
            new_task = database.get_task(task_id)
            if new_task:
                database.update_task_status(task_id, "running")
                self.orchestrator.schedule_task(new_task)
            self.refresh_task_list()
        else:
            self.log("❌ Failed to create task.")

    def refresh_task_list(self):
        for widget in self.task_list_frame.winfo_children(): widget.destroy()
        self.task_widgets.clear()
        for i, task in enumerate(database.get_all_tasks()):
            frame = ctk.CTkFrame(self.task_list_frame)
            frame.grid(row=i, column=0, padx=5, pady=5, sticky="ew")
            frame.grid_columnconfigure(0, weight=1)
            desc = task["description"] or "Random Quote"
            schedule_text = f"ID {task['id']}: {desc} — "
            if task['task_type'] == 'one_time':
                run_dt = datetime.fromisoformat(task['run_datetime']).strftime('%Y-%m-%d %I:%M %p')
                schedule_text += f"One-Time at {run_dt}"
            elif task['task_type'] == 'recurring':
                schedule_text += f"Recurring {task['recurrence_rule']}"
            ctk.CTkLabel(frame, text=schedule_text, anchor="w").grid(row=0, column=0, padx=10, pady=10, sticky="ew")
            status_label = ctk.CTkLabel(frame, text=task['status'].capitalize(), width=100)
            status_label.grid(row=0, column=1, padx=10)
            button = ctk.CTkButton(frame, width=80, command=lambda tid=task['id']: self.toggle_task(tid))
            button.grid(row=0, column=2, padx=5)
            ctk.CTkButton(frame, text="Delete", fg_color="#D32F2F", hover_color="#B71C1C", command=lambda tid=task['id']: self.delete_task(tid)).grid(row=0, column=3, padx=5)
            self.task_widgets[task['id']] = {"status_label": status_label, "button": button}
            self.update_task_widget_status(task['id'], task['status'])
            
    def process_queue(self):
        try:
            while not self.update_queue.empty():
                msg = self.update_queue.get_nowait()
                if msg["type"] == "log": self.log(msg["message"])
                elif msg["type"] == "error": self.log(f"❌ {msg['message']}")
                elif msg["type"] == "status_update": self.update_task_widget_status(msg["task_id"], msg["status"])
                elif msg["type"] == "task_deleted": self.remove_task_widget(msg["task_id"])
                elif msg["type"] == "show_windows_notification":
                    self._show_windows_toast(msg["message"])
        finally:
            self.after(200, self.process_queue)

    def _show_windows_toast(self, message: str):
        if WINDOWS_TOASTS_AVAILABLE:
            try:
                toaster = WindowsToaster('Mind Set')
                new_toast = Toast()
                new_toast.text_fields = ["Mind Set Reminder", message]
                toaster.show_toast(new_toast)
                self.log(f"✅ Windows notification sent.")
            except Exception as e:
                self.log(f"❌ Failed to send Windows toast: {e}")

    def remove_task_widget(self, task_id):
        if task_id in self.task_widgets:
            self.task_widgets[task_id]["status_label"].master.destroy()
            del self.task_widgets[task_id]
            self.log(f"🗑️ Task {task_id} completed and removed.")

    def toggle_task(self, task_id):
        task = database.get_task(task_id)
        if not task: return
        if task['status'] == "running":
            database.update_task_status(task_id, "stopped")
            self.orchestrator.unschedule_task(task_id)
        else: 
            database.update_task_status(task_id, "running")
            self.orchestrator.schedule_task(task)

    def delete_task(self, task_id):
        self.orchestrator.unschedule_task(task_id)
        database.delete_task(task_id)
        self.log(f"🗑️ Task {task_id} deleted.")
        self.refresh_task_list()

    def update_task_widget_status(self, task_id, status):
        if task_id not in self.task_widgets: return
        widgets = self.task_widgets[task_id]
        status_colors = {"running": "green", "stopped": "orange", "completed": "gray50", "error": "red"}
        widgets["status_label"].configure(text=status.capitalize(), text_color=status_colors.get(status, "white"))
        if status == "running": widgets["button"].configure(text="Stop", fg_color="#D32F2F", hover_color="#B71C1C")
        else: widgets["button"].configure(text="Start", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])

    def on_date_focus(self, event):
        if not self.date_entry.get(): self.date_entry.insert(0, datetime.now().strftime('%m/%d/%Y'))
    def on_time_focus(self, event):
        if not self.time_entry.get(): self.time_entry.insert(0, (datetime.now() + timedelta(minutes=1)).strftime('%H:%M'))
    def log(self, message):
        print(message)
        self.status_label.configure(text=message)
    def open_settings(self): SettingsWindow(self)
    def on_closing(self):
        self.log("Shutting down orchestrator...")
        self.orchestrator.shutdown()
        self.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    app = App()
    app.mainloop()