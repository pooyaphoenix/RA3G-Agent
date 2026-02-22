"""
PostgreSQL store for encrypted PII and document metadata.
Links FAISS index (by faiss_id) to encrypted passage text.
"""
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.utils.logger import get_logger
from app.utils.pii_encryption import decrypt_pii, encrypt_pii, get_encryption_key_id

logger = get_logger("db", "logs/gateway.log")

_ENGINE = None
_SESSION_FACTORY = None


def get_database_url() -> Optional[str]:
    return os.getenv("DATABASE_URL")


def is_pg_storage_enabled() -> bool:
    url = get_database_url()
    if not url:
        return False
    return os.getenv("USE_PG_STORAGE", "").lower() in ("true", "1", "yes")


def _get_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    url = get_database_url()
    if not url:
        return None
    try:
        _ENGINE = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)
        _ENGINE.connect()
        logger.info("PostgreSQL connection established")
        return _ENGINE
    except Exception as e:
        logger.warning("PostgreSQL not available: %s", e)
        return None


def _get_session_factory():
    global _SESSION_FACTORY
    if _SESSION_FACTORY is not None:
        return _SESSION_FACTORY
    engine = _get_engine()
    if engine is None:
        return None
    _SESSION_FACTORY = sessionmaker(engine, autocommit=False, autoflush=False)
    return _SESSION_FACTORY


@contextmanager
def session_scope():
    """Context manager for a single DB session."""
    factory = _get_session_factory()
    if factory is None:
        raise RuntimeError("PostgreSQL not configured")
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_schema(sess: Optional[Session] = None):
    """Create tables if they do not exist."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS pii_records (
        id SERIAL PRIMARY KEY,
        record_type VARCHAR(50) DEFAULT 'passage',
        encrypted_data BYTEA NOT NULL,
        encryption_key_id VARCHAR(100) DEFAULT 'default',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        source_file VARCHAR(255) NOT NULL,
        passage_index INTEGER NOT NULL,
        faiss_id INTEGER NOT NULL,
        pii_record_id INTEGER REFERENCES pii_records(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(faiss_id)
    );
    CREATE TABLE IF NOT EXISTS query_logs (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        query_text TEXT,
        redacted_response TEXT,
        governance_decision JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_documents_faiss_id ON documents(faiss_id);
    CREATE INDEX IF NOT EXISTS idx_query_logs_session ON query_logs(session_id);
    CREATE INDEX IF NOT EXISTS idx_query_logs_created ON query_logs(created_at);
    """
    if sess is not None:
        for stmt in schema_sql.strip().split(";"):
            if stmt.strip():
                sess.execute(text(stmt))
        return
    with session_scope() as s:
        for stmt in schema_sql.strip().split(";"):
            if stmt.strip():
                s.execute(text(stmt))
    logger.info("Schema initialized")


def insert_passage(faiss_id: int, source_file: str, passage_index: int, passage_data: Dict[str, Any]) -> None:
    """Store one passage: encrypt text into pii_records, then link in documents."""
    encrypted = encrypt_pii(passage_data)
    key_id = get_encryption_key_id()
    with session_scope() as sess:
        init_schema(sess)
        r = sess.execute(
            text(
                "INSERT INTO pii_records (record_type, encrypted_data, encryption_key_id) "
                "VALUES ('passage', :data, :kid) RETURNING id"
            ),
            {"data": encrypted, "kid": key_id},
        )
        pii_id = r.scalar()
        if pii_id is None:
            raise RuntimeError("INSERT pii_records did not return id")
        sess.execute(
            text(
                "INSERT INTO documents (source_file, passage_index, faiss_id, pii_record_id) "
                "VALUES (:src, :pidx, :fid, :pii_id) "
                "ON CONFLICT (faiss_id) DO UPDATE SET pii_record_id = EXCLUDED.pii_record_id"
            ),
            {"src": source_file, "pidx": passage_index, "fid": faiss_id, "pii_id": pii_id},
        )


def get_passage_by_faiss_id(faiss_id: int) -> Optional[Dict[str, Any]]:
    """Load one passage by FAISS index; decrypt and return dict with id, text, source."""
    with session_scope() as sess:
        r = sess.execute(
            text(
                "SELECT pr.encrypted_data FROM documents d "
                "JOIN pii_records pr ON d.pii_record_id = pr.id WHERE d.faiss_id = :fid"
            ),
            {"fid": faiss_id},
        )
        row = r.fetchone()
    if not row:
        return None
    return decrypt_pii(row[0])


def get_all_passages_ordered_by_faiss_id() -> List[Dict[str, Any]]:
    """Load all passages in faiss_id order (for RetrieverAgent.meta)."""
    with session_scope() as sess:
        r = sess.execute(
            text(
                "SELECT pr.encrypted_data FROM documents d "
                "JOIN pii_records pr ON d.pii_record_id = pr.id ORDER BY d.faiss_id"
            )
        )
        rows = r.fetchall()
    return [decrypt_pii(row[0]) for row in rows]


def save_passages_batch(meta: List[Dict[str, Any]]) -> None:
    """Replace all stored passages with the given list (same order as FAISS index)."""
    with session_scope() as sess:
        init_schema(sess)
        sess.execute(text("TRUNCATE documents RESTART IDENTITY CASCADE"))
        sess.execute(text("TRUNCATE pii_records RESTART IDENTITY CASCADE"))
    for i, passage in enumerate(meta):
        insert_passage(i, passage.get("source", ""), i, passage)
    logger.info("Saved %d passages to PostgreSQL", len(meta))


def insert_query_log(
    session_id: str,
    query_text: Optional[str] = None,
    redacted_response: Optional[str] = None,
    governance_decision: Optional[Dict] = None,
) -> None:
    """Append one query to audit log."""
    if not is_pg_storage_enabled():
        return
    try:
        import json
        with session_scope() as sess:
            sess.execute(
                text(
                    "INSERT INTO query_logs (session_id, query_text, redacted_response, governance_decision) "
                    "VALUES (:sid, :q, :resp, :gov::jsonb)"
                ),
                {
                    "sid": session_id,
                    "q": query_text,
                    "resp": redacted_response,
                    "gov": json.dumps(governance_decision) if governance_decision else None,
                },
            )
    except Exception as e:
        logger.warning("Failed to write query_log: %s", e)
