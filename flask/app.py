import os
from flask import Flask, render_template, g
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__, template_folder='templates')

def get_conn():
    if 'conn' not in g:
        g.conn = pymysql.connect(
            host=os.environ.get('DB_HOST','mysql'),
            port=int(os.environ.get('DB_PORT',3306)),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASS'),
            database=os.environ.get('DB_NAME'),
            cursorclass=DictCursor,
            autocommit=True
        )
    return g.conn

@app.route('/')
def index():
    return '<h3>App Flask (read-only) — ir a <a href="/app/tabla">/app/tabla</a></h3>'

@app.route('/app/tabla')
def tabla():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, customer, item, qty, created_at FROM orders ORDER BY created_at DESC LIMIT 200;")
        rows = cur.fetchall()
    return render_template('tabla.html', rows=rows)

@app.teardown_appcontext
def close_conn(exc):
    conn = g.pop('conn', None)
    if conn:
        conn.close()
