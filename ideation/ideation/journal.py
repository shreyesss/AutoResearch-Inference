"""Small command journal; no environment values or provider error text."""
import datetime as dt
import json
import sqlite3
import uuid


def connect(root):
    path = root / 'commands.sqlite'
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS commands (id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT, command TEXT, arguments TEXT, outcome TEXT, error_type TEXT)')
    archived = root / 'research/command-history.sqlite'
    if archived.is_file():
        source = sqlite3.connect(archived.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            db.executemany('INSERT OR IGNORE INTO commands VALUES(?,?,?,?,?,?,?)', source.execute('SELECT id,started_at,finished_at,command,arguments,outcome,error_type FROM commands'))
            db.commit()
        finally:
            source.close()
    return db


def start(root, args):
    identifier = uuid.uuid4().hex
    # File contents, raw query text, environment and arbitrary argument values
    # are deliberately absent; query/run details live in explicit run records.
    allowed = ('command', 'backfill_command', 'hypothesis_command', 'experiment_command', 'namespace',
               'after', 'before', 'limit', 'offline', 'reason', 'deep_count', 'recent_days', 'repo')
    fields = {k: getattr(args, k) for k in allowed if hasattr(args, k)}
    with connect(root) as db:
        db.execute('INSERT INTO commands VALUES(?,?,?,?,?,?,?)', (identifier, dt.datetime.now(dt.timezone.utc).isoformat(), None, args.command, json.dumps(fields), 'started', None))
    db.close()
    return identifier


def finish(root, identifier, error=None):
    with connect(root) as db:
        db.execute('UPDATE commands SET finished_at=?,outcome=?,error_type=? WHERE id=?',
                   (dt.datetime.now(dt.timezone.utc).isoformat(), 'failed' if error else 'succeeded', type(error).__name__ if error else None, identifier))
    db.close()


def history(root, limit=20):
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    db = connect(root)
    db.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in db.execute('SELECT * FROM commands ORDER BY started_at DESC LIMIT ?', (limit,))]
        for row in rows:
            row['arguments'] = json.loads(row['arguments'])
        return {'commands': rows, 'note': 'started without finish means in-flight or interrupted, not success; command completions publish with next snapshot'}
    finally:
        db.close()
