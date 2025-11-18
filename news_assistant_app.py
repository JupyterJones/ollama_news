from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory
import sqlite3
import os
import datetime
from icecream import ic

app = Flask(__name__)

DB_FILE = 'news.db'
AUDIO_DIR = 'audio'
TEXT_DIR = 'texts'

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)

# -----------------------------
# Database Setup
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT UNIQUE,
                    created_at TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS narrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    text TEXT,
                    audio_file TEXT,
                    created_at TEXT,
                    FOREIGN KEY(query_id) REFERENCES queries(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    narration_id INTEGER,
                    url TEXT,
                    FOREIGN KEY(narration_id) REFERENCES narrations(id)
                )''')
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Helpers
# -----------------------------
def get_conn():
    return sqlite3.connect(DB_FILE)

def get_query(query_text):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM queries WHERE query=?", (query_text,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def add_query(query_text):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO queries(query, created_at) VALUES (?, ?)", (query_text, now))
    conn.commit()
    query_id = get_query(query_text)
    conn.close()
    return query_id

def add_narration(query_id, text, audio_file, urls):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO narrations(query_id, text, audio_file, created_at) VALUES (?, ?, ?, ?)",
              (query_id, text, audio_file, now))
    narration_id = c.lastrowid
    for u in urls:
        c.execute("INSERT INTO articles(narration_id, url) VALUES (?, ?)", (narration_id, u))
    conn.commit()
    conn.close()
    return narration_id

def get_narrations(query_id, limit=None):
    conn = get_conn()
    c = conn.cursor()
    q = "SELECT id, text, audio_file, created_at FROM narrations WHERE query_id=? ORDER BY created_at DESC"
    if limit:
        q += f" LIMIT {limit}"
    c.execute(q, (query_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_articles(narration_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT url FROM articles WHERE narration_id=?", (narration_id,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def delete_narration(narration_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT audio_file FROM narrations WHERE id=?", (narration_id,))
    audio = c.fetchone()
    if audio and audio[0] and os.path.exists(audio[0]):
        os.remove(audio[0])
    c.execute("DELETE FROM articles WHERE narration_id=?", (narration_id,))
    c.execute("DELETE FROM narrations WHERE id=?", (narration_id,))
    conn.commit()
    conn.close()

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, query, created_at FROM queries ORDER BY created_at DESC")
    queries = c.fetchall()
    conn.close()
    return render_template_string('''
    <h1>News Assistant</h1>
    <form action="/search">
        <input type="text" name="q" placeholder="Search...">
        <input type="submit" value="Go">
    </form>
    <h2>Past Queries</h2>
    <ul>
    {% for q in queries %}
        <li><a href="/query/{{q[0]}}">{{q[1]}}</a></li>
    {% endfor %}
    </ul>
    ''', queries=queries)

@app.route('/search')
def search():
    q = request.args.get('q')
    if not q:
        return redirect(url_for('index'))
    query_id = add_query(q)
    return redirect(url_for('query_view', query_id=query_id))

@app.route('/query/<int:query_id>')
def query_view(query_id):
    narrations = get_narrations(query_id, limit=3)
    return render_template_string('''
    <h1>Query</h1>
    <a href="/">Home</a> | <a href="/older/{{query_id}}">Older Versions</a>
    <h2>Latest Narrations</h2>
    {% for n in narrations %}
        <div style="border:1px solid #ccc; margin:10px; padding:10px;">
            <p><b>{{n[3]}}</b></p>
            <p>{{n[1]}}</p>
            {% if n[2] %}<audio controls src="/{{n[2]}}"></audio>{% endif %}
            <ul>
            {% for link in get_articles(n[0]) %}
                <li><a href="{{link}}" target="_blank">{{link}}</a></li>
            {% endfor %}
            </ul>
            <form method="post" action="/delete/{{n[0]}}">
                <input type="submit" value="Delete">
            </form>
        </div>
    {% endfor %}
    ''', narrations=narrations, get_articles=get_articles, query_id=query_id)

@app.route('/older/<int:query_id>')
def older(query_id):
    narrations = get_narrations(query_id)
    return render_template_string('''
    <h1>Older Versions</h1>
    <a href="/query/{{query_id}}">Back</a>
    {% for n in narrations %}
        <div style="border:1px solid #ccc; margin:10px; padding:10px;">
            <p><b>{{n[3]}}</b></p>
            <p>{{n[1]}}</p>
            {% if n[2] %}<audio controls src="/{{n[2]}}"></audio>{% endif %}
            <ul>
            {% for link in get_articles(n[0]) %}
                <li><a href="{{link}}" target="_blank">{{link}}</a></li>
            {% endfor %}
            </ul>
            <form method="post" action="/delete/{{n[0]}}">
                <input type="submit" value="Delete">
            </form>
        </div>
    {% endfor %}
    ''', narrations=narrations, get_articles=get_articles, query_id=query_id)

@app.route('/delete/<int:narration_id>', methods=['POST'])
def delete(narration_id):
    delete_narration(narration_id)
    return redirect(request.referrer or url_for('index'))

@app.route('/<path:filename>')
def serve_file(filename):
    if filename.startswith(AUDIO_DIR):
        return send_from_directory('.', filename)
    return "Not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
