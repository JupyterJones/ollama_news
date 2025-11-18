

#import ollama
import asyncio
import sqlite3
import datetime
import httpx
from icecream import ic
# --- Configuration ---


OLLAMA_URL = "http://31.97.146.63:11444/api/generate"
OLLAMA_MODEL = "mistral:7b"


MODEL_NAME = "phi3:mini"
DB_NAME = "chat_history.db"

def setup_database():
    """Sets up the SQLite database and table."""
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

def save_dialogue(speaker, dialogue):
    """Saves a piece of dialogue to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (speaker, dialogue, timestamp) VALUES (?, ?, ?)",
        (speaker, dialogue, datetime.datetime.now())
    )
    conn.commit()
    conn.close()

OLLAMA_URL = "http://31.97.146.63:11444/api/generate"
MODEL_NAME = "phi3:mini"

async def run_interactive_chat():
    print(f"--- Starting Interactive Podcast Banter with {MODEL_NAME} ---")
    print("Type 'exit' or 'quit' to end the session.")
    messages=[]
    async with httpx.AsyncClient(timeout=None) as client:
        prompt = [
            {
                'role': 'system',
                'content': 'You are a creative co-host on a science fiction podcast. Your name is Gemni. The user is your co-host, Jack. Engage in a fun, creative banter about sci-fi topics.'
            }
        ]

        while True:
            try:
                prompt_text = input("\nJack: ")
                if prompt_text.strip() == "":
                    continue
                if prompt_text.lower() in ["exit", "quit"]:
                    print("\n--- End of Session ---")
                    break

                # Save Jack's message
                save_dialogue("Jack", prompt_text)
                messages.append({'role': 'user', 'content': prompt_text})

                # Send the request to the LLM
                print("\nGemni: ", end="", flush=True)
                full_response = ""

                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "messages": messages,
                        "stream": True
                    },
                    headers={"Accept": "application/x-ndjson"}
                )

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        part = httpx.Response.json(httpx.Response(200, content=line))
                        chunk = part['message']['content']
                        print(chunk, end='', flush=True)
                        full_response += chunk
                    except Exception as e:
                        ic(f"Stream parse error: {e}")
                        continue

                # Save Gemni's full reply
                save_dialogue("Gemni", full_response)
                messages.append({'role': 'assistant', 'content': full_response})

            except (KeyboardInterrupt, EOFError):
                print("\n--- End of Session ---")
                break
            except Exception as e:
                ic(f"An error occurred: {e}")
                break



if __name__ == "__main__":
    # Set up the database first
    setup_database()

    # Run the async interactive chat session
    asyncio.run(run_interactive_chat())

