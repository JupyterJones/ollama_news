import aiohttp
import asyncio
import sqlite3
import json
from icecream import ic

# ====== CONFIG ======
DB_FILE = "scifi_chat.db"
#VPS_URL = "http://31.97.146.63:11444/api/chat"
#MODEL_NAME = "phi3:mini"
# --- Configuration ---
MODEL_NAME = "mistral:7b"  # Must match the model loaded on your VPS
VPS_URL = "http://31.97.146.63:11444/api/chat"  # VPS Ollama chat endpoint

# ====== DATABASE ======
def setup_database():
    ic("Setting up database...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS dialogue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speaker TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()
    ic("Database ready.")

def save_message(speaker, message):
    ic(f"Saving dialogue for: {speaker}")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO dialogue (speaker, message) VALUES (?, ?)", (speaker, message))
    conn.commit()
    conn.close()
    ic(f"Saved {speaker} message.")

# ====== VPS CHAT ======
async def query_vps(messages):
    """Send chat messages to the VPS and return a single complete response."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }
    ic(f"Connecting to VPS at {VPS_URL}")
    async with aiohttp.ClientSession() as session:
        async with session.post(VPS_URL, json=payload) as resp:
            ic(f"Connected, HTTP status: {resp.status}")
            data = await resp.json()
            ic("Response JSON received", data)
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            return "[No response from VPS]"

# ====== MAIN LOOP ======
async def main():
    setup_database()

    messages = [
        {"role": "system", "content": (
            "You are a creative co-host on a science fiction podcast. "
            "Your name is Ollama. The user is your co-host, Jack. "
            "Engage in a fun, creative banter about sci-fi topics."
        )}
    ]

    print(f"--- Starting Interactive Podcast Banter with {MODEL_NAME} (VPS) ---")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        user_input = input("Jack: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        save_message("Jack", user_input)
        messages.append({"role": "user", "content": user_input})

        response_text = await query_vps(messages)
        # After receiving response_text from VPS
        clean_text = "\n".join(
            line for line in response_text.splitlines()
            if not line.strip().startswith("## Instruction")
        )
        print(f"Ollama: {clean_text}")
        save_message("Ollama", clean_text)
        '''

        print(f"Ollama: {response_text}")

        save_message("Ollama", response_text)
        messages.append({"role": "assistant", "content": response_text})
        '''
if __name__ == "__main__":
    asyncio.run(main())
