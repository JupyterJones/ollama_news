#!/usr/bin/env python3
# fishing.py
import requests
from bs4 import BeautifulSoup
from icecream import ic
import time
import random
import sys
import html
import re
import os
import json
import datetime
import chromadb
import requests
from chromadb.utils import embedding_functions
import glob
import hashlib

# ==== CONFIG ====
HTML_DIR = "html_pages"   # Folder with saved HTML files
ARTICLES_JSON = "articles.json"
CHROMA_DIR = "chroma_storage"
CHUNK_SIZE = 500  # words per chunk
CHUNK_OVERLAP = 50  # overlap between chunks for context

# ==== INIT CHROMADB ====
client = chromadb.PersistentClient(path=CHROMA_DIR)
embedding_func = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="news_articles",
    embedding_function=embedding_func
)

# ==== LOAD EXISTING JSON ARCHIVE ====
if os.path.exists(ARTICLES_JSON):
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles_archive = json.load(f)
else:
    articles_archive = []

# Quick duplicate check
existing_urls = {a["url"] for a in articles_archive}

# ==== HELPERS ====
def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += size - overlap
    return chunks

def extract_article_text(html_content):
    """Extract visible text content from HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def safe_filename(name):
    """Make a filesystem-safe version of a string."""
    safe = re.sub(r'[^A-Za-z0-9]+', '_', name)
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_')[:100]

# ==== PROCESS HTML FILES ====
def process_html():
    new_articles = []
    for html_file in glob.glob(os.path.join(HTML_DIR, "*.html")):
        ic(f"Processing {html_file}")

        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # The file itself might contain multiple articles from fishing.py
        article_links = soup.select("h2 a[href]")
        if not article_links:
            ic(f"⚠ No article links found in {html_file}, skipping.")
            continue

        for link_tag in article_links:
            url = link_tag.get("href")
            title = link_tag.get_text(strip=True) or "Untitled"

            # Skip duplicates
            if not url or url in existing_urls:
                if url:
                    ic(f"✅ Already stored: {url}")
                continue

            # Extract cleaned text
            article_text = extract_article_text(html_content)
            if len(article_text) < 100:
                ic(f"⚠ Not enough text for {url}, skipping.")
                continue

            # Chunk for embeddings
            chunks = chunk_text(article_text)

            # Store in ChromaDB
            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5((url + str(i)).encode()).hexdigest()
                collection.add(
                    documents=[chunk],
                    metadatas=[{
                        "title": title,
                        "url": url,
                        "filename": os.path.basename(html_file),
                        "chunk_index": i,
                        "scraped_date": datetime.datetime.now().strftime("%Y-%m-%d")
                    }],
                    ids=[chunk_id]
                )

            # Save in archive JSON
            articles_archive.append({
                "title": title,
                "url": url,
                "filename": os.path.basename(html_file),
                "chunks": len(chunks),
                "scraped_date": datetime.datetime.now().strftime("%Y-%m-%d")
            })
            new_articles.append(url)
            existing_urls.add(url)

    # ==== WRITE UPDATED ARCHIVE ====
    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles_archive, f, indent=2, ensure_ascii=False)

    ic(f"🎯 Added {len(new_articles)} new articles to ChromaDB.")
# ---------------- CONFIG ----------------
TTS_API_URL   = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "af_sky"
OUTPUT_DIR    = "tts_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# ----------------------------------------


def sanitize_filename(text: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", text.strip())
    return (safe[:20] or "tts_audio") + ".mp3"


def generate_tts(text: str) -> str:
    payload = {"input": text, "voice": ASSISTANT_VOICE}
    try:
        resp = requests.post(TTS_API_URL, json=payload, timeout=630)
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

def narrate(OUTPUT_FILE):
    # ==== CONFIG ====
    CHROMA_DIR = "chroma_storage"
    COLLECTION_NAME = "news_articles"
    #MISTRAL_URL = "http://31.97.146.63:11444/v1/chat/completions"
    #PHI_URL = "http://localhost:11434/api/generate"
    PHI_URL = "http://localhost:11434/v1/chat/completions"

    #PHI_URL = "http://localhost:11434/v1/chat/completions" 
    MAX_RESULTS = 12  # top chunks to send

    # ==== INIT CHROMADB ====
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_func = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func
    )

    # ==== GET QUERY ====
    if len(sys.argv) < 2:
        query = "Kings River beaver lake"
    else:
        query = " ".join(sys.argv[1:])

    ic(f"🔍 Searching ChromaDB for: {query}")

    # ==== SEARCH IN CHROMADB ====
    results = collection.query(
        query_texts=[query],
        n_results=MAX_RESULTS
    )

    # Flatten the documents
    chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not chunks:
        ic("⚠ No results found in ChromaDB.")
        sys.exit(0)

    # ==== PREPARE RAW TEXT FOR SAVING ====
    raw_news_text = "\n\n".join(
        f"[{meta.get('title', 'No title')}] {chunk}"
        for chunk, meta in zip(chunks, metadatas)
    )

    # ==== SEND TO PHI-3 ====
    prompt = (
        f"Based on the following retrieved news excerpts, write a flowing, engaging narration "
        f"suitable for a YouTube Latest News channel. Do not copy sentences directly — paraphrase "
        f"and merge ideas into a smooth story. Use a natural storytelling tone, as if a human presenter "
        f"is reading live on air. Keep it clear, professional, and engaging.\n\n"
        f"News excerpts:\n{raw_news_text}\n\n"
        f"Now write the final narration:"
    )

    payload = {
        "model": "phi3:latest",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional YouTube news narrator. Your job is to take raw article excerpts and rewrite them into smooth narration scripts. Speak naturally, avoid lists, and sound like a human broadcaster."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    '''

    # ==== SEND TO PHI ====
    prompt = (
        f"You are a professional news narrator for YouTube.\n"
        f"Based on the following retrieved news excerpts, write a flowing, engaging narration "
        f"suitable for a YouTube Latest News channel. Avoid plagiarism by paraphrasing and merging ideas. "
        f"Make it sound like it’s being read aloud by a human presenter.\n\n"
        f"News excerpts:\n{raw_news_text}\n\n"
        f"Now write the final narration:"
    )

    payload = {
        "model": "phi3:latest",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant and professional news narrator and find the latest news on Arkansas"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    '''
    try:
        r = requests.post(PHI_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=560)
        r.raise_for_status()
        response_data = r.json()
        narration = response_data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        ic(f"❌ Error contacting PHI API: {e}")
        sys.exit(1)

    # ==== SAVE TO FILE ====
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        #f.write(f"=== YouTube Narration ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
        f.write(narration)
        f.write("\n")
        #f.write(raw_news_text)

    ic(f"✅ Narration saved to {OUTPUT_FILE}")

    # ==== PRINT TO SCREEN ====
    print("\n" + "="*40)
    print("🎙 YouTube Narration:")
    print("="*40)
    print(narration)
    print("="*40)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

def safe_filename(name):
    """
    Convert a string into a safe filename:
    - Replace non-alphanumeric characters with underscores
    - Collapse multiple underscores
    - Strip leading/trailing underscores
    - Limit length to 100 chars to avoid OS issues
    """
    safe = re.sub(r'[^A-Za-z0-9]+', '_', name)
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('_')
    return safe[:100]  # safety limit

def search_articles(query, num_results=20):
    """Scrape DuckDuckGo HTML search results with pagination."""
    url = "https://html.duckduckgo.com/html/"
    results = []
    page_size = 10

    for start in range(0, num_results, page_size):
        params = {"q": query, "s": str(start)}
        try:
            response = requests.post(url, headers=HEADERS, data=params, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            ic("HTTP/Connection Error:", e)
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        for result in soup.select(".result"):
            title_tag = result.select_one(".result__title a")
            snippet_tag = result.select_one(".result__snippet")
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag.get("href", "")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet
                })
        if len(results) >= num_results:
            break

    return results[:num_results]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ic("Usage: python fishing.py <search terms>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    ic(f"🎣 Searching DuckDuckGo for: {query}")

    articles = search_articles(query)
    ic(f"Found {len(articles)} items.")

    # Ensure the output directory exists
    os.makedirs("html_pages", exist_ok=True)

    # Build HTML content
    html_content = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        f"<meta charset='utf-8'><title>DuckDuckGo Search Results for {html.escape(query)}</title>",
        "<style>body { font-family: Arial; max-width: 800px; margin: auto; } h2 { margin-bottom: 5px; } p { color: #555; }</style>",
        "</head>",
        "<body>",
        f"<h1>DuckDuckGo Search Results for: {html.escape(query)}</h1>",
        "<hr>"
    ]

    for article in articles:
        html_content.append(
            f"<h2><a href='{html.escape(article['url'])}' target='_blank'>{html.escape(article['title'])}</a></h2>"
        )
        if article['snippet']:
            html_content.append(f"<p>{html.escape(article['snippet'])}</p>")
        html_content.append("<br>")

    html_content.append("</body></html>")

    # Create a fully safe filename
    safe_name = safe_filename(query)
    filename = f"html_pages/{safe_name}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(html_content))

    ic(f"Results saved to {filename}")

    # Sleep to be polite to DuckDuckGo
    for _ in range(len(articles[:15])):
        time.sleep(random.uniform(0.5, 1.5))
    process_html()
    safe_name = safe_filename(query)
    OUTPUT_FILE = f"{safe_name}.txt"
    ic(f"OUTPUT_FILE: {OUTPUT_FILE}")
    narrate(OUTPUT_FILE)
    text = open(OUTPUT_FILE).read()
    ic(text)
    generate_tts(text)