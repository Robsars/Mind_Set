# tasks.py
import aiohttp
import config
import json
import random

STATE_FILE = 'state.json'

def _read_state():
    """Reads the current state from the state file."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"recently_shown_indices": []}

def _save_state(state):
    """Saves the given state to the state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

async def get_random_quote_with_cooldown():
    """
    Selects a truly random quote, avoiding the last 10 that were shown.
    """
    try:
        with open('quotes.json', 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        
        if not quotes:
            return "Quote file is empty."

        state = _read_state()
        recently_shown = state.get("recently_shown_indices", [])
        
        all_indices = set(range(len(quotes)))
        forbidden_indices = set(recently_shown)
        available_indices = list(all_indices - forbidden_indices)
        
        if not available_indices:
            available_indices = list(all_indices)

        chosen_index = random.choice(available_indices)
        quote = quotes[chosen_index]
        
        recently_shown.append(chosen_index)
        updated_history = recently_shown[-10:]
        
        state["recently_shown_indices"] = updated_history
        _save_state(state)

        author = quote.get("author", "Unknown")
        return f"\"{quote['text']}\" - {author}"

    except (FileNotFoundError, IndexError):
        return "Could not retrieve a quote."

async def send_pushover_notification(message: str):
    """Sends a notification ONLY to the Pushover service."""
    api_token = config.get_secret(config.PUSHOVER_API_SERVICE, "api_token")
    user_key = config.get_secret(config.PUSHOVER_USER_SERVICE, "user_key")

    if not api_token or not user_key:
        print("❌ Pushover API token or user key not found.")
        return

    url = "https://api.pushover.net/1/messages.json"
    payload = {"token": api_token, "user": user_key, "message": message, "title": "Mind Set Reminder"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    print(f"✅ Pushover notification sent: '{message}'")
                else:
                    print(f"❌ Failed to send Pushover notification. Status: {response.status}")
    except aiohttp.ClientError as e:
        print(f"❌ Network error on Pushover request: {e}")