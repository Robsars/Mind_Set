# orchestrator.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import database
from tasks import send_pushover_notification, get_random_quote_with_cooldown

class Orchestrator:
    def __init__(self, update_queue):
        self.scheduler = AsyncIOScheduler()
        self.update_queue = update_queue # FIXED

    async def _run_task(self, task_id: int, description: str, task_type: str):
        """The job logic that runs in the background thread."""
        message = description
        if not description:
            message = await get_random_quote_with_cooldown()
        
        self.update_queue.put({"type": "log", "message": f"▶️ Executing task {task_id}: '{message}'"})
        
        # 1. Send the Pushover notification from the background thread
        await send_pushover_notification(message)
        
        # 2. Ask the main UI thread to show the Windows notification
        self.update_queue.put({"type": "show_windows_notification", "message": message})
        
        if task_type == 'one_time':
            database.delete_task(task_id)
            self.update_queue.put({"type": "task_deleted", "task_id": task_id})

    def schedule_task(self, task):
        task_id, job_id = task['id'], f"task_{task['id']}"
        description = task['description'] or ""
        if self.scheduler.get_job(job_id): self.scheduler.remove_job(job_id)
        trigger_args, task_type = {}, task['task_type']
        if task_type == 'one_time':
            trigger_args = {'trigger': 'date', 'run_date': datetime.fromisoformat(task['run_datetime'])}
        elif task_type == 'recurring':
            cron_fields = ['month', 'day_of_month', 'day_of_week', 'hour', 'minute']
            cron_args = {field: task[f'recurrence_{field}'] for field in cron_fields if task[f'recurrence_{field}'] is not None}
            trigger_args = {'trigger': 'cron', **cron_args}
        if trigger_args:
            self.scheduler.add_job(self._run_task, **trigger_args, args=[task_id, description, task_type], id=job_id)
            self.update_queue.put({"type": "log", "message": f"✅ Task {task_id} scheduled."})
            self.update_queue.put({"type": "status_update", "task_id": task_id, "status": "running"})
            
    def unschedule_task(self, task_id):
        job_id = f"task_{task_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            self.update_queue.put({"type": "log", "message": f"⏹️ Task {task_id} unscheduled."})
            self.update_queue.put({"type": "status_update", "task_id": task_id, "status": "stopped"})
            
    def start(self):
        self.scheduler.start()
        self.update_queue.put({"type": "log", "message": "Orchestrator started."})
        for task in database.get_tasks_by_status("running"):
            self.schedule_task(task)
            
    def shutdown(self):
        self.update_queue.put({"type": "log", "message": "Orchestrator shutting down."})
        self.scheduler.shutdown()