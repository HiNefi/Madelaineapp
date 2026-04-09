import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", "love_messages.db")


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    message     TEXT    NOT NULL,
                    schedule_time TEXT  NOT NULL,
                    created_at  TEXT    NOT NULL,
                    sent        INTEGER DEFAULT 0,
                    sent_at     TEXT
                )
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add_message(self, message: str, schedule_time: str):
        """Insert a new scheduled message."""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (message, schedule_time, created_at, sent) VALUES (?,?,?,0)",
                (message, schedule_time, created_at),
            )
            conn.commit()

    def mark_sent(self, message_id: int):
        """Mark a message as sent and record the timestamp."""
        sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE messages SET sent=1, sent_at=? WHERE id=?",
                (sent_at, message_id),
            )
            conn.commit()

    def delete_message(self, message_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE id=?", (message_id,))
            conn.commit()

    # ------------------------------------------------------------------
    # Read – active lists (shown in Buenos Días / Buenas Noches windows)
    # ------------------------------------------------------------------
    def get_active_messages(self, schedule_time: str) -> list[dict]:
        """
        Returns:
          • All UNSENT messages for this schedule slot.
          • Messages SENT within the last 24 h (still visible in the list).
        Order: unsent first (oldest → newest), then sent (oldest sent_at first).
        """
        cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE schedule_time = ?
                  AND (sent = 0 OR (sent = 1 AND sent_at > ?))
                ORDER BY sent ASC, created_at ASC
                """,
                (schedule_time, cutoff),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Read – sent archive (shown in Enviados window)
    # ------------------------------------------------------------------
    def get_sent_messages(self) -> list[dict]:
        """Messages sent MORE than 24 h ago (moved to the archive)."""
        cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM messages
                WHERE sent = 1 AND sent_at <= ?
                ORDER BY sent_at DESC
                """,
                (cutoff,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------
    def get_next_unsent(self, schedule_time: str) -> dict | None:
        """Oldest unsent message for the given slot (the one to send next)."""
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM messages
                WHERE schedule_time = ? AND sent = 0
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (schedule_time,),
            ).fetchone()
        return dict(row) if row else None
