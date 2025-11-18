#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kokoro_tts_generate.py
Generate MP3 audio from text via Kokoro TTS.

Usage:
    python kokoro_tts_generate.py "Hello world"
"""

import os
import sys
import re
import requests
from icecream import ic
import sqlite3

# --- Source Configuration ---
DB_NAME = "chat_history.db"
OUTPUT_DIR = "podcast_audio"

# ---------------- CONFIG ----------------
TTS_API_URL   = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE_F = "af_sky"
ASSISTANT_VOICE_M = "am_adam"
OUTPUT_DIR    = "tts_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# ----------------------------------------


def sanitize_filename(text: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", text.strip())
    return (safe[:20] or "tts_audio") + ".mp3"


def generate_af_sky(text: str) -> str:
    payload = {"input": text, "voice": ASSISTANT_VOICE_F}
    try:
        resp = requests.post(TTS_API_URL, json=payload, timeout=330)
        resp.raise_for_status()
        file_name = sanitize_filename(text)
        file_path = os.path.join(OUTPUT_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(resp.content)
        ic(f"TTS audio saved → {file_path}")
        return file_path
    except Exception as e:
        ic(f"TTS generation failed: {e}")
        return None

def generate_am_adam(text: str) -> str:
    payload = {"input": text, "voice": ASSISTANT_VOICE_M}
    try:
        resp = requests.post(TTS_API_URL, json=payload, timeout=330)
        resp.raise_for_status()
        file_name = sanitize_filename(text)
        file_path = os.path.join(OUTPUT_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(resp.content)
        ic(f"TTS audio saved → {file_path}")
        return file_path
    except Exception as e:
        ic(f"TTS generation failed: {e}")
        return None

def fetch_dialogue():
    """Fetches all dialogue from the database, ordered by timestamp."""
    if not os.path.exists(DB_NAME):
        print(f"Error: Database file '{DB_NAME}' not found.")
        return None
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Fetching id, speaker, and dialogue, ordered by ID to maintain conversation flow
    cursor.execute("SELECT id, speaker, dialogue FROM conversations ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def main():
    """Main function to generate the audio files."""
    print("--- Starting Podcast Audio Generation ---")

    # 1. Fetch dialogue from the database
    dialogues = fetch_dialogue()
    if not dialogues:
        print("No dialogue found in the database. Exiting.")
        return

    # 2. Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Audio files will be saved in '{OUTPUT_DIR}/'")

    # 3. Initialize the TTS models
    # This might take a while on the first run as models are downloaded.
    print("Initializing TTS models... (This may take some time)")
    try:
        ic(len(dialogues))
        #tts_gemni = generate_af_sky(text)
        #tts_jack = generate_am_adam(text)
        print("TTS models loaded successfully.")
    except Exception as e:
        print(f"Error initializing TTS models: {e}")
        return

    # 4. Process each line of dialogue
    print("Generating audio files...")
    for row_id, speaker, text in dialogues:
        ic(f"SPEAKER: {speaker}")
        '''
        ic(f"ROW_ID: {row_id}")
        # Format the filename to be sortable, e.g., 001_Jack.wav
        filename = f"{row_id:03d}_{speaker}.mp3"
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(output_path):
            print(f"  - Skipping existing file: {output_path}")
            continue

        print(f"Processing: {filename}")
        '''
        try:
            if speaker.lower() == 'gemini':
                # Generate audio for Gemni
                output_path = generate_af_sky(text)
            elif speaker.lower() == 'jack':
                # Generate audio for Jack using the specific speaker from the model
                output_path = generate_am_adam(text)
            else:
                print(f"  - Skipping unknown speaker: {speaker}")
                continue
            
            print(f"  - Saved: {output_path}")

        except Exception as e:
            print(f"  - Error generating audio for '{text}': {e}")

    print("\n--- Audio Generation Complete ---")


if __name__ == '__main__':
    main()









'''


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ic("Usage: python kokoro_tts_generate.py 'Your text here'")
        sys.exit(1)

    content = sys.argv[1]

    text = open(content, "r").read()
    ic(f"Input text: {text}")

    mp3_path = generate_tts(text)
    if mp3_path:
        ic("Done!")
    else:
        sys.exit(1)

'''        