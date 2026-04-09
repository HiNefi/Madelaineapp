import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "./data/love_messages.db")

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        # NO llamar _init_db aquí → se hará al primer uso
        self._conn = None

    def _get_conn(self):
        if self._conn is None or not self._conn.closed:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                schedule_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                sent BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()

    def add_message(self, message: str, schedule_time: str):
        self._init_db()  # Lazy init: solo al primer uso
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (message, schedule_time, created_at, sent) VALUES (?, ?, ?, 0)",
            (message, schedule_time, created_at)
        )
        conn.commit()

    def delete_message(self, msg_id: int):
        self._init_db()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()

    def get_pending(self, schedule_time: str):
        self._init_db()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, message, created_at, sent FROM messages WHERE schedule_time = ? ORDER BY sent ASC, created_at DESC",
            (schedule_time,)
        )
        rows = cursor.fetchall()
        return rows

    def mark_as_sent(self, msg_id: int):
        self._init_db()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET sent = 1 WHERE id = ?", (msg_id,))
        conn.commit()
