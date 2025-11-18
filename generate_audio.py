import sys
from unittest.mock import MagicMock

# --- Monkey-patching to prevent the problematic import ---
# This is a workaround for a persistent TypeError with the bangla phonemizer
# on this specific environment. We are telling Python to replace the bangla
# phonemizer module with a fake, empty object *before* TTS tries to import it.
MOCK_MODULES = [
    "TTS.tts.utils.text.phonemizers.bangla_phonemizer",
    "TTS.tts.utils.text.bangla",
    "TTS.tts.utils.text.bangla.phonemizer",
    "bangla"
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()
# --- End of Monkey-patch ---

import sqlite3
import os
from TTS.api import TTS

# --- Configuration ---
DB_NAME = "chat_history.db"
OUTPUT_DIR = "podcast_audio"

# --- Voice Models ---
# Using a standard, high-quality female voice for the AI, Gemni.
GEMNI_VOICE_MODEL = "tts_models/en/ljspeech/vits"

# Using a multi-speaker model for Jack to get a contrasting male voice.
# The VCTK corpus has many speakers. 'p226' is a standard male voice.
JACK_VOICE_MODEL = "tts_models/en/vctk/vits"
JACK_SPEAKER = "p226"

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
        tts_gemni = TTS(model_name=GEMNI_VOICE_MODEL, progress_bar=False)
        tts_jack = TTS(model_name=JACK_VOICE_MODEL, progress_bar=False)
        print("TTS models loaded successfully.")
    except Exception as e:
        print(f"Error initializing TTS models: {e}")
        print("Please ensure you have a working internet connection for the first run to download models.")
        return

    # 4. Process each line of dialogue
    print("Generating audio files...")
    for row_id, speaker, text in dialogues:
        # Format the filename to be sortable, e.g., 001_Jack.wav
        filename = f"{row_id:03d}_{speaker}.wav"
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        if os.path.exists(output_path):
            print(f"  - Skipping existing file: {output_path}")
            continue

        print(f"Processing: {filename}")

        try:
            if speaker.lower() == 'gemini':
                # Generate audio for Gemni
                tts_gemni.tts_to_file(text=text, file_path=output_path)
            elif speaker.lower() == 'jack':
                # Generate audio for Jack using the specific speaker from the model
                tts_jack.tts_to_file(text=text, speaker=JACK_SPEAKER, file_path=output_path)
            else:
                print(f"  - Skipping unknown speaker: {speaker}")
                continue
            
            print(f"  - Saved: {output_path}")

        except Exception as e:
            print(f"  - Error generating audio for '{text}': {e}")

    print("\n--- Audio Generation Complete ---")

if __name__ == "__main__":
    main()