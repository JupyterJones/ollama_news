#!/usr/bin/env python3
# converse_with_alien.py
import sqlite3
import chromadb
from chromadb.config import Settings
from icecream import ic

# --- CONFIG ---
PERSIST_DIR = "./alien_chroma"
COLLECTION_NAME = "arcanian_entity"
SQLITE_FILE = "conversations.db"

# --- Initialize ChromaDB ---
client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_or_create_collection(COLLECTION_NAME)

# --- Initialize SQLite ---
conn = sqlite3.connect(SQLITE_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS dialogue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    ai_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- Simple retrieval from Chroma ---
def query_chroma(prompt, n_results=3):
    results = collection.query(
        query_texts=[prompt],
        n_results=n_results
    )
    docs = results.get("documents", [[]])[0]
    return "\n".join(docs)

# --- Save conversation to SQLite ---
def save_conversation(user_input, ai_response):
    cursor.execute(
        "INSERT INTO dialogue (user_input, ai_response) VALUES (?, ?)",
        (user_input, ai_response)
    )
    conn.commit()

# --- Main loop ---
def converse():
    print("Start chatting with the alien entity. Type 'exit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Alien: We remain when you leave.")
            break
        chroma_data = query_chroma(user_input)
        ai_response = chroma_data if chroma_data else "We resonate even in silence."
        print(f"Alien: {ai_response}")
        save_conversation(user_input, ai_response)

if __name__ == "__main__":
    converse()
