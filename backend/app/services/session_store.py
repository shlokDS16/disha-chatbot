from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import Settings
from app.errors import DishaError, ErrorCode
from app.models.schemas import (
    ConsentMethod,
    ConsentRecord,
    ConsentScope,
    Language,
    Persona,
    SessionState,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id     TEXT PRIMARY KEY,
    language       TEXT NOT NULL,
    persona        TEXT,
    consent_json   TEXT NOT NULL DEFAULT '{"accepted": false}',
    message_count  INTEGER NOT NULL DEFAULT 0,
    location_lat   REAL,
    location_lng   REAL,
    location_label TEXT,
    created_at     TEXT NOT NULL,
    last_activity  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id     TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL,
    role           TEXT NOT NULL,
    language       TEXT NOT NULL,
    text           TEXT NOT NULL,
    content_json   TEXT,
    source         TEXT,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS files (
    file_id       TEXT PRIMARY KEY,
    session_id    TEXT,
    filename      TEXT NOT NULL,
    path          TEXT NOT NULL,
    type          TEXT NOT NULL,
    size_bytes    INTEGER NOT NULL,
    status        TEXT NOT NULL,
    ocr_text      TEXT,
    summary_json  TEXT,
    error         TEXT,
    language      TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id TEXT PRIMARY KEY,
    message_id  TEXT NOT NULL,
    session_id  TEXT,
    rating      TEXT NOT NULL,
    reason      TEXT,
    comment     TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_files_session ON files(session_id);
"""


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


class SessionStore:
    """Synchronous SQLite-backed session + message + file + feedback store.

    SQLite is embedded; all calls are fast local disk ops. Using the stdlib
    driver keeps the dependency footprint small for a prototype.
    """

    def __init__(self, settings: Settings) -> None:
        self.db_path = settings.sqlite_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as c:
            c.executescript(SCHEMA)
            # Additive migrations for live dev DBs created before a column existed.
            for col, ddl in (
                ("location_lat", "ALTER TABLE sessions ADD COLUMN location_lat REAL"),
                ("location_lng", "ALTER TABLE sessions ADD COLUMN location_lng REAL"),
                ("location_label", "ALTER TABLE sessions ADD COLUMN location_label TEXT"),
            ):
                try:
                    c.execute(ddl)
                except sqlite3.OperationalError:
                    pass  # column already exists

    # ── Sessions ────────────────────────────────────────────────

    def create_session(self, language: Language, persona: Persona | None) -> SessionState:
        session_id = str(uuid.uuid4())
        now = _now_iso()
        consent = ConsentRecord(accepted=False)
        with self._conn() as c:
            c.execute(
                "INSERT INTO sessions (session_id, language, persona, consent_json, created_at, last_activity) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    language.value,
                    persona.value if persona else None,
                    consent.model_dump_json(),
                    now,
                    now,
                ),
            )
        return SessionState(
            session_id=session_id,
            language=language,
            persona=persona,
            consent=consent,
            message_count=0,
            created_at=_parse_iso(now),
            last_activity=_parse_iso(now),
        )

    def get_session(self, session_id: str) -> SessionState:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if not row:
            raise DishaError(
                ErrorCode.SESSION_NOT_FOUND,
                "Session not found.",
                status_code=404,
                details={"session_id": session_id},
            )
        return self._row_to_session(row)

    def update_language(self, session_id: str, language: Language) -> SessionState:
        with self._conn() as c:
            result = c.execute(
                "UPDATE sessions SET language = ?, last_activity = ? WHERE session_id = ?",
                (language.value, _now_iso(), session_id),
            )
            if result.rowcount == 0:
                raise DishaError(
                    ErrorCode.SESSION_NOT_FOUND, "Session not found.", status_code=404
                )
        return self.get_session(session_id)

    def record_consent(
        self,
        session_id: str,
        accepted: bool,
        method: ConsentMethod,
        scopes: list[ConsentScope],
    ) -> ConsentRecord:
        record = ConsentRecord(
            accepted=accepted,
            method=method,
            scopes=scopes,
            recorded_at=datetime.now(UTC),
        )
        with self._conn() as c:
            result = c.execute(
                "UPDATE sessions SET consent_json = ?, last_activity = ? WHERE session_id = ?",
                (record.model_dump_json(), _now_iso(), session_id),
            )
            if result.rowcount == 0:
                raise DishaError(
                    ErrorCode.SESSION_NOT_FOUND, "Session not found.", status_code=404
                )
        return record

    def delete_session(self, session_id: str, purge: bool = True) -> bool:
        with self._conn() as c:
            if purge:
                c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                c.execute("DELETE FROM files WHERE session_id = ?", (session_id,))
                c.execute("DELETE FROM feedback WHERE session_id = ?", (session_id,))
            result = c.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            return result.rowcount > 0

    def update_location(
        self, session_id: str, lat: float, lng: float, label: str | None
    ) -> SessionState:
        with self._conn() as c:
            result = c.execute(
                "UPDATE sessions SET location_lat = ?, location_lng = ?, "
                "location_label = ?, last_activity = ? WHERE session_id = ?",
                (lat, lng, label, _now_iso(), session_id),
            )
            if result.rowcount == 0:
                raise DishaError(
                    ErrorCode.SESSION_NOT_FOUND, "Session not found.", status_code=404
                )
        return self.get_session(session_id)

    def increment_message_count(self, session_id: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE sessions SET message_count = message_count + 1, last_activity = ? WHERE session_id = ?",
                (_now_iso(), session_id),
            )

    # ── Messages ────────────────────────────────────────────────

    def save_message(
        self,
        session_id: str,
        role: str,
        language: Language,
        text: str,
        content: list[dict[str, Any]] | None = None,
        source: str | None = None,
    ) -> str:
        message_id = str(uuid.uuid4())
        with self._conn() as c:
            c.execute(
                "INSERT INTO messages (message_id, session_id, role, language, text, content_json, source, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    message_id,
                    session_id,
                    role,
                    language.value,
                    text,
                    json.dumps(content) if content else None,
                    source,
                    _now_iso(),
                ),
            )
        self.increment_message_count(session_id)
        return message_id

    def get_recent_messages(
        self, session_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT message_id, role, language, text, source, created_at "
                "FROM messages WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def export_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        with self._conn() as c:
            messages = [
                dict(r)
                for r in c.execute(
                    "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at",
                    (session_id,),
                ).fetchall()
            ]
            files = [
                dict(r)
                for r in c.execute(
                    "SELECT file_id, filename, type, status, created_at FROM files WHERE session_id = ?",
                    (session_id,),
                ).fetchall()
            ]
        return {
            "session": session.model_dump(mode="json"),
            "messages": messages,
            "files": files,
        }

    # ── Feedback ────────────────────────────────────────────────

    def save_feedback(
        self,
        feedback_id: str,
        message_id: str,
        session_id: str | None,
        rating: str,
        reason: str | None,
        comment: str | None,
    ) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO feedback (feedback_id, message_id, session_id, rating, reason, comment, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (feedback_id, message_id, session_id, rating, reason, comment, _now_iso()),
            )

    # ── Files ───────────────────────────────────────────────────

    def save_file_record(
        self,
        file_id: str,
        session_id: str | None,
        filename: str,
        path: str,
        ftype: str,
        size_bytes: int,
    ) -> None:
        now = _now_iso()
        with self._conn() as c:
            c.execute(
                "INSERT INTO files (file_id, session_id, filename, path, type, size_bytes, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?)",
                (file_id, session_id, filename, path, ftype, size_bytes, now, now),
            )

    def update_file(self, file_id: str, **fields: Any) -> None:
        fields["updated_at"] = _now_iso()
        cols = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values())
        values.append(file_id)
        with self._conn() as c:
            c.execute(f"UPDATE files SET {cols} WHERE file_id = ?", values)

    def get_file(self, file_id: str) -> dict[str, Any]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)).fetchone()
        if not row:
            raise DishaError(
                ErrorCode.FILE_NOT_FOUND, "File not found.", status_code=404,
                details={"file_id": file_id},
            )
        return dict(row)

    def get_session_files(
        self, session_id: str, limit: int = 5, only_done: bool = True
    ) -> list[dict[str, Any]]:
        """Return recently uploaded, OCR'd files for this session."""
        sql = (
            "SELECT file_id, filename, type, status, ocr_text, summary_json, "
            "language, created_at FROM files WHERE session_id = ?"
        )
        params: tuple[Any, ...] = (session_id,)
        if only_done:
            sql += " AND status = 'done'"
        sql += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        with self._conn() as c:
            rows = c.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def delete_message(self, session_id: str, message_id: str) -> bool:
        with self._conn() as c:
            r = c.execute(
                "DELETE FROM messages WHERE message_id = ? AND session_id = ?",
                (message_id, session_id),
            )
            return r.rowcount > 0

    def clear_messages(self, session_id: str) -> int:
        with self._conn() as c:
            r = c.execute(
                "DELETE FROM messages WHERE session_id = ?", (session_id,)
            )
            c.execute(
                "UPDATE sessions SET message_count = 0, last_activity = ? "
                "WHERE session_id = ?",
                (_now_iso(), session_id),
            )
            return r.rowcount

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> SessionState:
        consent_data = json.loads(row["consent_json"] or '{"accepted": false}')
        keys = row.keys()
        lat = row["location_lat"] if "location_lat" in keys else None
        lng = row["location_lng"] if "location_lng" in keys else None
        label = row["location_label"] if "location_label" in keys else None
        location = (
            {"lat": lat, "lng": lng, "label": label}
            if lat is not None and lng is not None
            else None
        )
        return SessionState(
            session_id=row["session_id"],
            language=Language(row["language"]),
            persona=Persona(row["persona"]) if row["persona"] else None,
            consent=ConsentRecord(**consent_data),
            message_count=row["message_count"],
            location=location,
            created_at=_parse_iso(row["created_at"]),
            last_activity=_parse_iso(row["last_activity"]),
        )


_store_singleton: SessionStore | None = None


def get_session_store(settings: Settings) -> SessionStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = SessionStore(settings)
    return _store_singleton
