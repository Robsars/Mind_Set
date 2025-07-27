# database.py
import sqlite3
import config
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                task_type TEXT NOT NULL,           -- 'one_time' or 'recurring'
                run_datetime TIMESTAMP,          -- For 'one_time' tasks
                recurrence_rule TEXT,            -- 'minutely', 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
                recurrence_minute TEXT,          -- cron field
                recurrence_hour TEXT,            -- cron field
                recurrence_day_of_month TEXT,    -- cron field
                recurrence_day_of_week TEXT,     -- cron field
                recurrence_month TEXT,           -- cron field
                status TEXT NOT NULL DEFAULT 'stopped'
            );
        """)
        conn.commit()
    print("✅ Database initialized successfully.")

def create_task(task_data: dict):
    """Adds a new task to the database from a dictionary."""
    with get_db_connection() as conn:
        try:
            keys = [
                'description', 'task_type', 'run_datetime', 'recurrence_rule', 
                'recurrence_minute', 'recurrence_hour', 'recurrence_day_of_month', 
                'recurrence_day_of_week', 'recurrence_month'
            ]
            for key in keys:
                task_data.setdefault(key, None)

            conn.execute(
                """INSERT INTO tasks (description, task_type, run_datetime, recurrence_rule, 
                                   recurrence_minute, recurrence_hour, recurrence_day_of_month, 
                                   recurrence_day_of_week, recurrence_month, status) 
                   VALUES (:description, :task_type, :run_datetime, :recurrence_rule, 
                           :recurrence_minute, :recurrence_hour, :recurrence_day_of_month, 
                           :recurrence_day_of_week, :recurrence_month, 'stopped')""",
                task_data
            )
            conn.commit()
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            return None

def get_task(task_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

def get_all_tasks():
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()

def get_tasks_by_status(status="running"):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM tasks WHERE status = ?", (status,)).fetchall()

def update_task_status(task_id, status):
    with get_db_connection() as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()

def delete_task(task_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()