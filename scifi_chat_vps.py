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
    """Saves a piece of dialogue to the database."""
    ic(f"Saving dialogue for: {speaker}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (speaker, dialogue, timestamp) VALUES (?, ?, ?)",
        (speaker, dialogue, datetime.datetime.now())
    )
    conn.commit()
    conn.close()
    ic(f"Saved {speaker} message.")

async def query_vps_stream(messages):
    """
    Streams chat completion from the VPS Ollama server.
    Yields partial response chunks.
    """
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True
    }
    ic(f"Connecting to VPS at {VPS_URL} with payload:")
    ic(payload)

    async with aiohttp.ClientSession() as session:
        async with session.post(VPS_URL, json=payload, timeout=350) as resp:
            ic(f"Connected, HTTP status: {resp.status}")
            async for line in resp.content:
                ic(f"Raw line: {line}")
                if not line.strip():
                    continue
                try:
                    data = line.decode("utf-8")
                    ic(f"Decoded line: {data}")
                    if data.startswith("data:"):
                        data_json = eval(data[5:].strip())  # ⚠ Insecure if public input
                        ic(f"Parsed JSON: {data_json}")
                        if "message" in data_json:
                            chunk = data_json["message"]["content"]
                            ic(f"Chunk received: {chunk}")
                            yield chunk
                except Exception as e:
                    ic(f"Stream parse error: {e}")

async def run_interactive_chat():
    print(f"--- Starting Interactive Podcast Banter with {MODEL_NAME} (VPS) ---")
    print("Type 'exit' or 'quit' to end the session.")

    messages = [
        {
            "role": "system",
            "content": "You are a creative co-host on a science fiction podcast. Your name is Ollama. The user is your co-host, Jack. Engage in a fun, creative banter about sci-fi topics."
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
            ic(f"Messages so far: {messages}")

            print("\nOllama: ", end="", flush=True)
            full_response = ""
            async for chunk in query_vps_stream(messages):
                print(chunk, end="", flush=True)
                full_response += chunk

            save_dialogue("Ollama", full_response)
            messages.append({"role": "assistant", "content": full_response})
            ic(f"Ollama full response: {full_response}")

        except (KeyboardInterrupt, EOFError):
            print("\n--- End of Session ---")
            break
        except Exception as e:
            ic(f"Error: {e}")
            break

if __name__ == "__main__":
    setup_database()
    asyncio.run(run_interactive_chat())
