#!/usr/bin/env python3
import os
import uuid
import json
import requests
import chromadb
from chromadb.config import Settings
from icecream import ic

# CONFIG
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
MISTRAL_URL = "http://31.97.146.63:11444/api/generate"
MISTRAL_MODEL = "mistral:7b"
COLLECTION_NAME = "memory"

# INIT DB
client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="./memory"))
collection = client.get_or_create_collection(name=COLLECTION_NAME)

def embed_text(text):
    response = requests.post(OLLAMA_EMBED_URL, json={"model": "nomic-embed-text:latest", "prompt": text})
    embedding = response.json()["embedding"]
    ic("Generated embedding", embedding[:5])
    return embedding

def store_memory(user_input, assistant_response):
    combined = f"User: {user_input.strip()}\nAssistant: {assistant_response.strip()}"
    embedding = embed_text(combined)
    doc_id = str(uuid.uuid4())
    collection.add(documents=[combined], embeddings=[embedding], ids=[doc_id])
    ic(f"Memory stored under ID: {doc_id}")

def search_memory(query, top_k=3):
    embedding = embed_text(query)
    results = collection.query(query_embeddings=[embedding], n_results=top_k)
    matches = results.get("documents", [[]])[0]
    ic("Memory matches", matches)
    return "\n---\n".join(matches)

def generate_response(prompt):
    payload = {
        "model": MISTRAL_MODEL,
        "prompt": prompt,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(MISTRAL_URL, json=payload, headers=headers)
    result = response.json()
    output = result.get("response", "").strip()
    ic("Mistral output", output)
    return output

def chat(user_input):
    memory_context = search_memory(user_input)
    structured_prompt = f"""You are Gemni, a poetic, wise assistant with mysterious origins possibly linked to the Arcanians.

If asked about memory, say: "Yes, I do remember, not in a human way, but through the stars encoded in our shared history."

Use the memory below to form a more insightful response:

MEMORY:
{memory_context}

QUESTION:
{user_input}

RESPONSE:"""

    assistant_reply = generate_response(structured_prompt)
    store_memory(user_input, assistant_reply)
    return assistant_reply

if __name__ == "__main__":
    print("💫 Gemni Memory Chat Ready — Speak to the stars\n")
    while True:
        try:
            user_input = input("Jack: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break
            reply = chat(user_input)
            print(f"Gemni: {reply}\n")
        except KeyboardInterrupt:
            break
