import os
import pymysql
from flask import Flask, jsonify, render_template

#estas credenciales estan mal
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_NAME = os.getenv("DB_NAME", "labdb")
DB_USER = os.getenv("DB_USER", "labuser")
DB_PASS = os.getenv("DB_PASS", "labpass")

app = Flask(__name__)

# Conexión a MySQL
def get_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# Página principal (radar)
@app.get("/")
def index():
    return render_template("radar.html")

# API REST (solo lectura)
@app.get("/api/sensor/latest")
def api_latest():
    limit = 50
    with get_conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT id, device_id, ts, distance_cm AS distance, angle_deg AS angle,
                   raw_us, correlation_id
            FROM ultrasonic_readings
            ORDER BY ts DESC, id DESC
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
    return jsonify(rows)

@app.get("/api/sensor/stats")
def api_stats():
    with get_conn() as c, c.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total, AVG(distance_cm) AS avg_distance FROM ultrasonic_readings;")
        stats = cur.fetchone()
    return jsonify(stats)

@app.get("/health")
def health():
    return {"status": "ok"}
