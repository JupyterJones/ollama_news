#editchat_db.py
import sqlite3

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

def run_interactive_chat():
    """
    Runs an interactive chat session between the user (Jack) and the model (Gemni),
    saving the conversation to the database.
    """
    print(f"--- Starting Interactive Podcast Banter with {MODEL_NAME} ---")
    print("Type 'exit' or 'quit' to end the session.")
    
    client = ollama.AsyncClient()
    # The conversation history is maintained in this list
    messages = [{'role': 'system', 'content': 'You are a creative co-host on a science fiction podcast. Your name is Gemni. The user is your co-host, Jack. Engage in a fun, creative banter about sci-fi topics.'}]

    while True:
        try:
            # Get input from the user
            prompt_text = input("\nJack: ")
            if not prompt_text.strip(): # Ignore empty input
                continue
            
            if prompt_text.lower() in ["exit", "quit"]:
                print("\n--- End of Session ---")
                break

            # Save Jack's dialogue and add it to the history
            save_dialogue("Jack", prompt_text)
            messages.append({'role': 'user', 'content': prompt_text})
            
            # Stream the response from the model
            print("\nGemni: ", end="", flush=True)
            full_response = ""
            async for part in await client.chat(model=MODEL_NAME, messages=messages, stream=True):
                response_piece = part['message']['content']
                print(response_piece, end='', flush=True)
                full_response += response_piece
            
            # Save Gemni's full response and add it to the history
            save_dialogue("Gemni", full_response)
            messages.append({'role': 'assistant', 'content': full_response})

        except (KeyboardInterrupt, EOFError):
            print("\n--- End of Session ---")
            break
        except Exception as e:
            print(f"\n\nAn error occurred: {e}")
            break


if __name__ == "__main__":
    # Set up the database first
    setup_database()
