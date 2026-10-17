"""Append-only SQLite experiment ledger with resume-safe identities."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  utc TEXT NOT NULL,
                  campaign_id TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  entity_id TEXT NOT NULL,
                  payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_lookup
                  ON events(campaign_id, kind, entity_id, seq);
                CREATE TABLE IF NOT EXISTS identities (
                  campaign_id TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  entity_id TEXT NOT NULL,
                  digest TEXT NOT NULL,
                  first_event_seq INTEGER NOT NULL,
                  PRIMARY KEY(campaign_id, kind, entity_id)
                );
            """)

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def append(self, campaign_id: str, kind: str, entity_id: str, payload: dict[str, Any]) -> int:
        if not campaign_id or not kind or not entity_id:
            raise ValueError("campaign, kind and entity IDs are required")
        with self.connect() as db:
            cur = db.execute(
                "INSERT INTO events(utc,campaign_id,kind,entity_id,payload_json) VALUES(?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), campaign_id, kind, entity_id, _json(payload)),
            )
            return int(cur.lastrowid)

    def claim(self, campaign_id: str, kind: str, entity_id: str, digest: str,
              payload: dict[str, Any]) -> bool:
        """Record a unique effective proposal/config; same identity resumes, mismatches fail."""
        with self.connect() as db:
            row = db.execute(
                "SELECT digest FROM identities WHERE campaign_id=? AND kind=? AND entity_id=?",
                (campaign_id, kind, entity_id),
            ).fetchone()
            if row:
                if row["digest"] != digest:
                    raise ValueError(f"{kind} {entity_id} changed under an existing identity")
                return False
            cur = db.execute(
                "INSERT INTO events(utc,campaign_id,kind,entity_id,payload_json) VALUES(?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), campaign_id, kind, entity_id, _json(payload)),
            )
            db.execute(
                "INSERT INTO identities VALUES(?,?,?,?,?)",
                (campaign_id, kind, entity_id, digest, int(cur.lastrowid)),
            )
            return True

    def events(self, campaign_id: str, kind: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as db:
            if kind:
                rows = db.execute(
                    "SELECT * FROM events WHERE campaign_id=? AND kind=? ORDER BY seq",
                    (campaign_id, kind),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM events WHERE campaign_id=? ORDER BY seq", (campaign_id,)
                ).fetchall()
        return [dict(row) | {"payload": json.loads(row["payload_json"])} for row in rows]

    def latest(self, campaign_id: str, kind: str, entity_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM events WHERE campaign_id=? AND kind=? AND entity_id=? ORDER BY seq DESC LIMIT 1",
                (campaign_id, kind, entity_id),
            ).fetchone()
        return (dict(row) | {"payload": json.loads(row["payload_json"])}) if row else None
