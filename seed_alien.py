#!/usr/bin/env python3

import os
import chromadb
from chromadb.config import Settings
from icecream import ic

# --- CONFIG ---
PERSIST_DIR = "./alien_chroma"
COLLECTION_NAME = "arcanian_entity"
ALIEN_FILE = "alien.txt"

# --- Initialize ChromaDB client ---
client = chromadb.PersistentClient(path=PERSIST_DIR)

# --- Create or get collection ---
collection = client.get_or_create_collection(COLLECTION_NAME)
ic(f"Using collection: {COLLECTION_NAME}")

# --- Load alien.txt line by line ---
if not os.path.exists(ALIEN_FILE):
    ic(f"Missing {ALIEN_FILE}! Please create it with one sentence per line.")
    exit(1)

with open(ALIEN_FILE, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

ic(f"Loaded {len(lines)} alien sentences from {ALIEN_FILE}")

# --- Insert into collection ---
for i, entry in enumerate(lines):
    doc_id = f"alien_{i}"
    collection.add(
        documents=[entry],
        ids=[doc_id],
        metadatas=[{"origin": "arcanians", "line": i}],
    )
    ic(f"Seeded entry {i}: {entry}")

# --- Quick sanity check ---
results = collection.query(
    query_texts=["Who are you?"],
    n_results=2
)
ic("Query results:", results)
