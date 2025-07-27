# config.py
import os
import keyring
import json
from dotenv import load_dotenv

load_dotenv()

# --- Constants ---
DATABASE_PATH = os.getenv("DATABASE_PATH", "tasks.db")
PUSHOVER_API_SERVICE = os.getenv("PUSHOVER_API_SERVICE")
PUSHOVER_USER_SERVICE = os.getenv("PUSHOVER_USER_SERVICE")
STATE_FILE = 'state.json'

# --- Secret Management ---
def set_secret(service_name, username, secret):
    """Securely stores a secret in the OS keychain."""
    try:
        keyring.set_password(service_name, username, secret)
        print(f"✅ Secret for '{service_name}' stored successfully.")
    except Exception as e:
        print(f"❌ Could not store secret: {e}")

def get_secret(service_name, username):
    """Retrieves a secret from the OS keychain."""
    try:
        return keyring.get_password(service_name, username)
    except Exception as e:
        print(f"❌ Could not retrieve secret: {e}")
        return None

# --- State Management ---
def read_state():
    """Reads the current state from the state file."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default structure if the file is missing or corrupt
        return {
            "quote_index": 0,
            "recently_shown_indices": [],
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }

def save_state(state):
    """Saves the given state to the state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)