"""Database helpers: one SQLite connection per request, schema + demo data."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    conn.executescript((Path(__file__).with_name("schema.sql")).read_text())
    if not conn.execute("SELECT 1 FROM users").fetchone():      # demo data on first run
        t = now()
        uid = conn.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?,?,?)",
                           ("demo", generate_password_hash("demo123", method="pbkdf2:sha256"), t)).lastrowid
        for title, body in [
            ("Hello, Flask!", "This blog is built with Flask blueprints, Jinja templates and SQLite.\n\nLog in as demo / demo123 to write your own posts."),
            ("Why I like Jinja template inheritance", "One base template holds the layout. Every page only fills in its own block, so the navigation and footer stay consistent."),
            ("Notes on database design", "Posts belong to users and comments belong to posts. Foreign keys with ON DELETE CASCADE keep the data clean.")]:
            conn.execute("INSERT INTO posts (author_id, title, body, created_at, updated_at) VALUES (?,?,?,?,?)", (uid, title, body, t, t))
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
