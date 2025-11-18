#!/usr/bin/env python3
import aiohttp
import asyncio
import sqlite3
import datetime
from icecream import ic

# --- Configuration ---
MODEL_NAME = "phi3:mini"  # Must match the model loaded on your VPS
VPS_URL = "http://31.97.146.63:11444/api/chat"  # VPS Ollama chat endpoint
DB_NAME = "chat_history.db"

def setup_database():
    """Sets up the SQLite database and table."""
    ic("Setting up database...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        speaker TEXT NOT NULL,
        dialogue TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    )
    """)
    conn.commit()
    conn.close()
    ic("Database ready.")

def save_dialogue(speaker, dialogue):
    """Saves a piece of dialogue to the database, prepending the speaker name for TTS."""
    dialogue_with_speaker = f"{speaker}: {dialogue.strip()}"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (speaker, dialogue, timestamp) VALUES (?, ?, ?)",
        (speaker, dialogue_with_speaker, datetime.datetime.now())
    )
    conn.commit()
    conn.close()
    ic(f"Saved {speaker} message: {dialogue_with_speaker[:60]}…")

async def query_vps(messages):
    """
    Sends a full request to VPS Ollama server (non-streaming) and returns the complete assistant response.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False  # non-streaming for cleaner single response
    }
    ic(f"Connecting to VPS at {VPS_URL} with payload:", payload)
    async with aiohttp.ClientSession() as session:
        async with session.post(VPS_URL, json=payload) as resp:
            ic(f"Connected, HTTP status: {resp.status}")
            if resp.status != 200:
                raise RuntimeError(f"TTS VPS returned {resp.status}: {await resp.text()}")
            data = await resp.json()
            # Covert to string depending on VPS response format
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            elif "completion" in data:  # fallback
                return data["completion"]
            else:
                return str(data)

async def run_interactive_chat():
    print(f"--- Starting Interactive Podcast Banter with {MODEL_NAME} (VPS) ---")
    print("Type 'exit' or 'quit' to end the session.\n")

    messages = [
        {
            "role": "system",
            "content": "You are a creative co-host on a science fiction podcast. "
                       "Your name is Ollama. The user is your co-host, Jack. "
                       "Engage in fun, creative banter about sci-fi topics."
        }
    ]

    while True:
        try:
            prompt_text = input("\nJack: ")
            if not prompt_text.strip():
                continue
            if prompt_text.lower() in ["exit", "quit"]:
                print("\n--- End of Session ---")
                break

            save_dialogue("Jack", prompt_text)
            messages.append({"role": "user", "content": prompt_text})

            # Query VPS for assistant response (non-streaming)
            assistant_response = await query_vps(messages)
            print(f"\nOllama: {assistant_response}")

            save_dialogue("Ollama", assistant_response)
            messages.append({"role": "assistant", "content": assistant_response})

        except (KeyboardInterrupt, EOFError):
            print("\n--- End of Session ---")
            break
        except Exception as e:
            ic(f"Error: {e}")
            break

if __name__ == "__main__":
    setup_database()
    asyncio.run(run_interactive_chat())
