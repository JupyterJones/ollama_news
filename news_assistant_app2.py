from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re, os, hashlib
from icecream import ic
import chromadb
from chromadb.utils import embedding_functions

# ==== CONFIG ====
DB_FILE = "news.db"
NARRATION_DIR = "static/narrations"
os.makedirs(NARRATION_DIR, exist_ok=True)

TTS_API_URL = "http://localhost:8880/v1/audio/speech"
ASSISTANT_VOICE = "af_sky"

MISTRAL_URL = "http://31.97.146.63:11444/v1/chat/completions"
MAX_RESULTS = 12  # top chunks for Chroma query

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
}

app = Flask(__name__)

# ==== DATABASE HELPERS ====
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY, query TEXT, url TEXT, html TEXT, date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS narrations
                 (id INTEGER PRIMARY KEY, query TEXT, summary TEXT,
                  text_file TEXT, audio_file TEXT, date TEXT)""")
    conn.commit()
    conn.close()

def save_article(query, url, html):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO articles (query,url,html,date) VALUES (?,?,?,?)",
              (query, url, html, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_narration(query, summary, text_file, audio_file):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO narrations (query,summary,text_file,audio_file,date) VALUES (?,?,?,?,?)",
              (query, summary, text_file, audio_file, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_narrations(limit=3):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,query,summary,text_file,audio_file,date FROM narrations ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_older_narrations(offset=3):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,query,summary,text_file,audio_file,date FROM narrations ORDER BY id DESC LIMIT -1 OFFSET ?", (offset,))
    rows = c.fetchall()
    conn.close()
    return rows

# ==== UTILITIES ====
def safe_filename(text):
    first_chars = re.sub(r'[^a-zA-Z0-9 ]', '', text)[:25]
    parts = first_chars.split()
    snippet = "_".join(parts) if parts else "narration"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{snippet}_{timestamp}"

def duckduckgo_search(query, max_results=5):
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    try:
        resp = requests.post(url, data=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        ic(f"Error fetching search results: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for div in soup.select("div.result"):
        a = div.find("a", href=True)
        if a and a['href'].startswith("http"):
            href = a['href']
            try:
                page = requests.get(href, timeout=10)
                save_article(query, href, page.text)
                links.append((href, page.text))
            except Exception as e:
                ic(f"Failed to fetch {href}: {e}")
        if len(links) >= max_results:
            break
    return links

def build_chroma(articles):
    client = chromadb.Client()
    embedding_func = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection("temp_news", embedding_function=embedding_func)
    for idx, (url, html_content) in enumerate(articles):
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(" ", strip=True)
        if len(text) > 50:
            collection.add(documents=[text], metadatas=[{"url": url}], ids=[str(idx)])
    return collection

def summarize_with_mistral(query, collection):
    results = collection.query(query_texts=[query], n_results=MAX_RESULTS)
    chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    if not chunks:
        return "⚠ No results found."

    raw_news_text = "\n\n".join(f"[{meta.get('url','No URL')}] {chunk}" for chunk, meta in zip(chunks, metadatas))

    prompt = (
        f"You are a professional news narrator for YouTube.\n"
        f"Based on the following retrieved news excerpts, write a flowing, engaging narration "
        f"suitable for a YouTube Latest News channel. Avoid plagiarism by paraphrasing and merging ideas. "
        f"Make it sound like it’s being read aloud by a human presenter.\n\n"
        f"News excerpts:\n{raw_news_text}\n\n"
        f"Now write the final narration:"
    )

    payload = {
        "model": "mistral:7b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant and professional news narrator."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        r = requests.post(MISTRAL_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=560)
        r.raise_for_status()
        response_data = r.json()
        narration = response_data["choices"][0]["message"]["content"].strip()
        return narration
    except Exception as e:
        ic(f"❌ Error contacting Mistral API: {e}")
        return "⚠ Error generating narration."

def generate_tts(text, filename_base):
    txt_path = os.path.join(NARRATION_DIR, filename_base + ".txt")
    mp3_path = os.path.join(NARRATION_DIR, filename_base + ".mp3")

    with open(txt_path, "w") as f:
        f.write(text)

    payload = {"input": text, "voice": ASSISTANT_VOICE}
    try:
        resp = requests.post(TTS_API_URL, json=payload, timeout=500)
        resp.raise_for_status()
        with open(mp3_path, "wb") as f:
            f.write(resp.content)
        return txt_path, mp3_path
    except Exception as e:
        ic(f"TTS generation failed: {e}")
        return txt_path, None

# ==== FLASK ROUTES ====
@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        query = request.form["query"].strip()
        if not query:
            return redirect(url_for("index"))
        ic(query)
        articles = duckduckgo_search(query)
        if not articles:
            return "⚠ No results found for this query. Try manual refresh later."
        collection = build_chroma(articles)
        summary = summarize_with_mistral(query, collection)
        urls = [u for u,_ in articles]
        header_text = f"Query: {query}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nURLs: {' '.join(urls)}\n\n{summary}"
        base = safe_filename(summary)
        txt_path, mp3_path = generate_tts(header_text, base)
        save_narration(query, summary, os.path.basename(txt_path), os.path.basename(mp3_path))
        return redirect(url_for("index"))

    narrations = get_narrations()
    return render_template_string("""
    <h1>News Assistant</h1>
    <form method="post">
      <input name="query" placeholder="Enter your query" style="width:300px">
      <button type="submit">Search / Refresh</button>
    </form>
    <h2>Latest Narrations</h2>
    {% for n in narrations %}
      <div style="margin-bottom:20px;">
        <b>{{n[1]}}</b> ({{n[5]}})<br>
        <a href="{{ url_for('static', filename='narrations/' + n[3]) }}" target="_blank">View Text</a> |
        {% if n[4] %}
          <audio controls src="{{ url_for('static', filename='narrations/' + n[4]) }}"></audio>
        {% endif %}
        <p>{{n[2]}}</p>
      </div>
    {% endfor %}
    <a href="{{ url_for('older_versions') }}">Older Versions</a>
    """, narrations=narrations)

@app.route("/older_versions")
def older_versions():
    narrations = get_older_narrations()
    return render_template_string("""
    <h1>Older Versions</h1>
    {% for n in narrations %}
      <div style="margin-bottom:20px;">
        <b>{{n[1]}}</b> ({{n[5]}})<br>
        <a href="{{ url_for('static', filename='narrations/' + n[3]) }}" target="_blank">View Text</a> |
        {% if n[4] %}
          <audio controls src="{{ url_for('static', filename='narrations/' + n[4]) }}"></audio>
        {% endif %}
        <p>{{n[2]}}</p>
      </div>
    {% endfor %}
    <a href="{{ url_for('index') }}">Back to Latest</a>
    """, narrations=narrations)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
