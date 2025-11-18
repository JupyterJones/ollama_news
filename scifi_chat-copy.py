

import ollama
import asyncio
import sqlite3
import datetime

# --- Configuration ---
MODEL_NAME = "phi3:mini"
DB_NAME = "chat_history.db"
PROMPTS = [
    "Let's brainstorm a science fiction story. I want to start with a unique core concept. Can you give me three distinct ideas for a sci-fi world?",
    "Those are interesting. I like the second idea. Let's develop that. What is the central conflict or problem in a world where memories can be traded as a commodity?",
    "That's a great conflict. Now, let's create a protagonist. Who would be a compelling main character in this world? Give me a brief character sketch.",
    "Excellent. What is the inciting incident that kicks off the story for this character?",
    "Perfect. Thank you for the creative session!"
]

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

async def run_chat_session():
    """
    Runs a pre-scripted chat session with the Ollama model and saves it to the DB.
    """
    print(f"--- Starting Sci-Fi Story Brainstorming Session with {MODEL_NAME} ---")
    
    # Use a single client for the session
    client = ollama.AsyncClient()

    for i, prompt_text in enumerate(PROMPTS):
        print(f"\n[Prompt {i+1}]")
        print(f"You: {prompt_text}")
        save_dialogue("Jack", prompt_text)
        
        try:
            # Stream the response
            print(f"Model:")
            full_response = ""
            async for part in await client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt_text}], stream=True):
                response_piece = part['message']['content']
                print(response_piece, end='', flush=True)
                full_response += response_piece
            
            save_dialogue("Gemini", full_response)
            print("\n" + "-"*20)

        except Exception as e:
            print(f"\n\nAn error occurred while communicating with the Ollama model: {e}")
            print("Please ensure the Ollama server is running and the model is available.")
            return # Stop the session on error

    print("\n--- End of Session ---")


if __name__ == "__main__":
    # Set up the database first
    setup_database()

    # Run the async chat session
    # The ollama library will automatically pull the model if it's not present.
    asyncio.run(run_chat_session())

