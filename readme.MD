Mind Set - Advanced Task Scheduler
Mind Set is a modern Windows desktop application for scheduling a variety of notifications through the Pushover service. It combines a user-friendly graphical interface with a powerful and secure backend, allowing you to create one-time, advanced recurring, and sequential quote reminders.

Features
Modern GUI: A clean and intuitive user interface built with CustomTkinter for a native look and feel on Windows.

Multiple Task Types:

One-Time: Schedule a notification for a specific date and time. These tasks are automatically deleted after completion.

Recurring: Create complex, repeating schedules (e.g., Every Minute, Hourly, Daily, Weekly, Monthly, Yearly).

Leave the description field blank on a recurring task to receive sequential quotes instead of a custom message.

Secure Credential Storage: Your sensitive Pushover API keys are stored securely in the Windows Credential Manager, not in a plaintext file.

Persistent Task Storage: All scheduled tasks are saved in a local SQLite database, so they are remembered even after you restart the application.

Live Task Management: Start, stop, and delete tasks directly from the main dashboard with real-time status updates.

Sequential Quote Delivery: The random quote feature cycles through a list of 100 affirmations and sayings sequentially, remembering its position between application restarts.

Requirements
Windows OS

Python 3.7+

A Pushover account (you will need your User Key and an Application API Token).

Setup and Installation
The included start.bat script automates the entire setup process.

Step 1: Get the Files
Place all the project files in a single, empty folder. The required files are:

app_ui.py

orchestrator.py

database.py

config.py

tasks.py

quotes.json

state.json

requirements.txt

.env.example

start.bat

Step 2: Create the .env Configuration File
Find the file named .env.example and create a copy of it in the same folder. Rename the copy to .env. You do not need to edit this file unless you want to change the database file name.

Step 3: Run the Launcher
Double-click the start.bat file.

The first time you run it, the script will:

Create a local Python virtual environment (venv folder).

Install all the necessary libraries from requirements.txt.

Launch the Mind Set application.

On subsequent runs, it will simply activate the environment and start the app.

How to Use
1. Set Your Pushover Keys
When the application first opens, click the "Settings" button. Enter your Pushover API Token and User Key into the fields and click "Save New Secrets". This will store them securely in the Windows Credential Manager.

2. Create a Task
Select a task type: "One-Time" or "Recurring".

The form will dynamically change to show the relevant options.

Fill in the required fields (date, time, frequency, etc.).

To create a sequential quote task, choose "Recurring" and leave the description field blank.

Click "Schedule Task".

3. Manage Tasks
Your new task will appear in the list.

Click "Start" to activate the schedule. The status will change to "running".

Click "Stop" to pause a running task.

Click "Delete" to permanently remove a task.

The project is organized into a single folder containing all the necessary scripts and configuration files.

Mind-Set-Advanced/ (Root Project Folder)

app_ui.py

orchestrator.py

database.py

config.py

tasks.py

quotes.json

state.json

requirements.txt

.env.example

start.bat

(Auto-generated)

tasks.db

venv/

