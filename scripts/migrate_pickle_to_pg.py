#!/usr/bin/env python3
"""
Migrate existing index_meta.pkl to PostgreSQL (encrypted).
Run with: USE_PG_STORAGE=true DATABASE_URL=... ENCRYPTION_KEY=... python scripts/migrate_pickle_to_pg.py
"""
import os
import sys
import pickle
from pathlib import Path

# Run from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

META_PATH = Path("app/index_meta.pkl")


def main():
    if not META_PATH.exists():
        print(f"Nothing to migrate: {META_PATH} not found.")
        return 0
    if not os.getenv("DATABASE_URL"):
        print("Set DATABASE_URL to run migration.")
        return 1
    os.environ.setdefault("USE_PG_STORAGE", "true")
    if not os.getenv("ENCRYPTION_KEY"):
        print("Warning: ENCRYPTION_KEY not set; using ephemeral key (not for production).")

    from app.db.store import save_passages_batch, init_schema, is_pg_storage_enabled

    if not is_pg_storage_enabled():
        print("USE_PG_STORAGE is not enabled.")
        return 1

    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    print(f"Loaded {len(meta)} passages from {META_PATH}")

    init_schema()
    save_passages_batch(meta)
    print("Migration done. Passages are now stored encrypted in PostgreSQL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
