"""Read-only live corpus reads must include committed WAL, unlike frozen replicas."""
import sqlite3

import pytest

from ideation.store import Store


def test_live_readonly_sees_committed_wal_and_rejects_writes(tmp_path):
    path = tmp_path / 'corpus.sqlite'
    writer = Store(path)
    try:
        writer.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        writer.db.execute('PRAGMA wal_autocheckpoint=0')
        writer.put({'id': 'report:new', 'source': 'analysis', 'kind': 'report',
                    'url': 'local:report:new', 'title': 'Projected result reuse',
                    'body': 'A committed report remains in the WAL before checkpoint.'})
        writer.db.commit()
        assert path.with_name(path.name + '-wal').stat().st_size > 0
        reader = Store(path, readonly=True)
        try:
            assert reader.get('report:new') is not None
            assert [r['id'] for r in reader.search('Projected result', match='all')] == ['report:new']
            assert len(reader.revisions('report:new')) == 1
            with pytest.raises(sqlite3.OperationalError, match='readonly'):
                reader.db.execute("DELETE FROM documents WHERE id='report:new'")
        finally:
            reader.db.close()
    finally:
        writer.db.close()


def test_frozen_replica_reads_without_creating_sidecars(tmp_path):
    path = tmp_path / 'corpus.sqlite'
    writer = Store(path)
    writer.put({'id': 'report:frozen', 'source': 'analysis', 'kind': 'report',
                'url': 'local:frozen', 'title': 'Frozen report', 'body': 'Snapshot contents'})
    writer.db.commit()
    writer.db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    writer.db.close()
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    reader = Store(path, readonly=True, immutable=True)
    try:
        assert reader.get('report:frozen')['body'] == 'Snapshot contents'
        with pytest.raises(sqlite3.OperationalError, match='readonly'):
            reader.db.execute('DELETE FROM documents')
    finally:
        reader.db.close()
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_invalid_immutable_and_missing_readonly_do_not_initialize(tmp_path):
    path = tmp_path / 'absent' / 'corpus.sqlite'
    with pytest.raises(ValueError, match='requires readonly'):
        Store(path, immutable=True)
    with pytest.raises(sqlite3.OperationalError):
        Store(path, readonly=True)
    assert not path.parent.exists()
