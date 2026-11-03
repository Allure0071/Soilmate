"""Backup and apply the additive event schema v3 to the Soilmate research DB."""

import argparse
import hashlib
import sqlite3
from pathlib import Path

from backend.app.agent.migration_v3 import migrate_event_schema

COUNTS = ("projects", "datasets", "samples", "analysis_runs", "research_actions", "reports", "users", "agent_tasks", "agent_events")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def counts(con):
    return {name: con.execute("SELECT COUNT(*) FROM " + name).fetchone()[0] for name in COUNTS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("backup", type=Path)
    args = parser.parse_args()
    if not args.database.is_file() or args.backup.exists():
        raise SystemExit("database missing or backup already exists")
    args.backup.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(args.database.as_uri() + "?mode=ro", uri=True)
    before = counts(source)
    backup = sqlite3.connect(args.backup)
    source.backup(backup)
    source.close()
    if counts(backup) != before or backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise SystemExit("backup verification failed; migration not attempted")
    backup.close()
    with sqlite3.connect(args.database) as live:
        applied = migrate_event_schema(live)
        after = counts(live)
        foreign_key_errors = live.execute("PRAGMA foreign_key_check").fetchall()
        version = live.execute("SELECT max(version) FROM schema_migrations").fetchone()[0]
    print({"applied": applied, "schema_version": version, "old_counts_unchanged": before == after,
           "foreign_key_errors": len(foreign_key_errors), "backup_sha256": sha(args.backup),
           "backup_path": str(args.backup)})
    if before != after or foreign_key_errors:
        raise SystemExit("post-migration verification failed")


if __name__ == "__main__":
    main()
