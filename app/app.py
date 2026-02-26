import os
import sqlite3
import glob
import time
from datetime import datetime
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

app = Flask(__name__)

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------- Routes ----------

@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")

@app.get("/add")
def add():
    init_db()

    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )

@app.get("/consultation")
def consultation():
    init_db()

    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )

    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]

    conn.close()

    return jsonify(rows)

@app.get("/count")
def count():
    init_db()

    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()

    return jsonify(count=n)

@app.route('/status', methods=['GET'])
def status():
    # 1. Compter les messages dans la base
    # On se connecte directement à la base via le chemin défini dans les variables d'environnement
    db_path = os.environ.get('DB_PATH', '/data/app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ATTENTION: Si ta table ne s'appelle pas "messages", change le nom ici !
    cursor.execute('SELECT COUNT(*) FROM events') 
    count = cursor.fetchone()[0]
    conn.close()

    # 2. Trouver le dernier backup et son âge
    list_of_files = glob.glob('/backup/*.db')
    
    if not list_of_files:
        return jsonify({
            "count": count,
            "last_backup_file": "Aucun",
            "backup_age_seconds": 0
        })

    # Récupère le fichier le plus récent
    latest_file = max(list_of_files, key=os.path.getmtime)
    file_name = os.path.basename(latest_file)
    
    # Calcule l'âge en secondes
    file_age = int(time.time() - os.path.getmtime(latest_file))

    return jsonify({
        "count": count,
        "last_backup_file": file_name,
        "backup_age_seconds": file_age
    })

    
# ---------- Main ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
