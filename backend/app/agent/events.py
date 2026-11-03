"""SQLite-backed at-least-once event transport with transactional fan-out and inbox."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Callable

from .contracts import AgentEvent


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat()


def _event_from_row(row):
    data = dict(row)
    return AgentEvent.model_validate({
        "event_id": data["id"], "event_type": data["event_type"],
        "event_version": data["event_version"], "occurred_at": data["occurred_at"],
        "producer": {"type": data["producer_type"], "id": data["producer_id"]},
        "task_id": data["task_id"], "conversation_id": data["conversation_id"],
        "plan_version": data["plan_version"], "step_id": data["step_id"],
        "session_id": data["session_id"], "correlation_id": data["correlation_id"],
        "causation_id": data["causation_id"], "idempotency_key": data["idempotency_key"],
        "payload": json.loads(data["payload_json"]),
    })


class EventStore:
    def append(self, con: sqlite3.Connection, event: AgentEvent) -> tuple[str, int | None, bool]:
        """Append event and outbox in caller's business transaction."""
        encoded = json.dumps(event.payload, ensure_ascii=False, sort_keys=True)
        prior = con.execute("SELECT id,event_type,payload_json,task_event_seq,task_id,conversation_id FROM agent_events WHERE idempotency_key=?",
                            (event.idempotency_key,)).fetchone()
        if prior:
            if (prior[1] != event.event_type or prior[2] != encoded or
                    prior[4] != event.task_id or prior[5] != event.conversation_id):
                raise ValueError("idempotency key reused for different event")
            return prior[0], prior[3], False
        sequence = None
        if event.task_id:
            con.execute("INSERT OR IGNORE INTO task_event_counters(task_id,last_seq) VALUES(?,0)", (event.task_id,))
            con.execute("UPDATE task_event_counters SET last_seq=last_seq+1 WHERE task_id=?", (event.task_id,))
            sequence = con.execute("SELECT last_seq FROM task_event_counters WHERE task_id=?", (event.task_id,)).fetchone()[0]
        con.execute("""INSERT INTO agent_events(id,task_id,conversation_id,event_type,event_version,occurred_at,
            producer_type,producer_id,plan_version,step_id,session_id,correlation_id,causation_id,
            idempotency_key,payload_json,task_event_seq) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (event.event_id, event.task_id, event.conversation_id, event.event_type, event.event_version,
             iso(event.occurred_at), event.producer.type, event.producer.id, event.plan_version,
             event.step_id, event.session_id, event.correlation_id, event.causation_id,
             event.idempotency_key, encoded, sequence))
        con.execute("""INSERT INTO event_outbox(event_id,status,attempts,created_at,next_attempt_at)
            VALUES(?,'pending',0,?,?)""", (event.event_id, iso(utc_now()), iso(utc_now())))
        return event.event_id, sequence, True

    def replay(self, con: sqlite3.Connection, task_id: str, after_seq: int = 0) -> list[dict]:
        rows = con.execute("""SELECT * FROM agent_events WHERE task_id=? AND task_event_seq>?
                              ORDER BY task_event_seq""", (task_id, after_seq)).fetchall()
        return [{"task_event_seq": row["task_event_seq"], "event": _event_from_row(row).model_dump(mode="json")}
                for row in rows]


class EventDispatcher:
    def __init__(self, connection_factory: Callable, max_attempts: int = 3):
        self.connection_factory = connection_factory
        self.max_attempts = max_attempts

    def dispatch_once(self, now: datetime | None = None) -> str | None:
        """Persist inbox fan-out, then mark outbox delivered in the same short transaction."""
        stamp = iso(now or utc_now())
        with self.connection_factory() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("""SELECT e.*,o.attempts,o.max_attempts AS outbox_max FROM event_outbox o JOIN agent_events e ON e.id=o.event_id
                WHERE o.status='pending' AND o.attempts<o.max_attempts AND
                (o.next_attempt_at IS NULL OR o.next_attempt_at<=?) ORDER BY e.rowid LIMIT 1""", (stamp,)).fetchone()
            if row is None:
                return None
            event_id = row["id"]
            try:
                target = json.loads(row["payload_json"]).get("target_consumer", "manager")
                targets = [target] if isinstance(target, str) else target
                if not targets or any(not isinstance(t, str) or not t for t in targets):
                    raise ValueError("invalid target_consumer")
                for consumer in targets:
                    con.execute("""INSERT OR IGNORE INTO consumer_inbox
                        (consumer_id,event_id,status,attempts,max_attempts,next_attempt_at)
                        VALUES(?,?,'pending',0,?,?)""", (consumer, event_id, self.max_attempts, stamp))
                con.execute("UPDATE event_outbox SET status='delivered',delivered_at=? WHERE event_id=?", (stamp, event_id))
                return event_id
            except Exception as exc:
                attempts = row["attempts"] + 1
                con.execute("UPDATE event_outbox SET attempts=?,last_error=?,next_attempt_at=? WHERE event_id=?",
                            (attempts, str(exc)[:500], iso((now or utc_now()) + timedelta(seconds=2 ** attempts)), event_id))
                if attempts >= row["outbox_max"]:
                    con.execute("""INSERT OR REPLACE INTO event_outbox_deadletters VALUES(?,?,?,?)""",
                                (event_id, attempts, str(exc)[:500], stamp))
                return None

    def consume_once(self, consumer_id: str, handler: Callable, now: datetime | None = None) -> str | None:
        """Run a short database-only handler atomically with inbox acknowledgement."""
        stamp = iso(now or utc_now())
        chosen = None
        try:
            with self.connection_factory() as con:
                con.execute("BEGIN IMMEDIATE")
                row = con.execute("""SELECT e.*,i.attempts AS inbox_attempts,i.max_attempts AS inbox_max
                    FROM consumer_inbox i JOIN agent_events e ON e.id=i.event_id
                    WHERE i.consumer_id=? AND i.status='pending' AND (i.next_attempt_at IS NULL OR i.next_attempt_at<=?)
                    AND NOT EXISTS (
                      SELECT 1 FROM consumer_inbox earlier JOIN agent_events prev ON prev.id=earlier.event_id
                      WHERE earlier.consumer_id=i.consumer_id AND prev.task_id=e.task_id
                      AND prev.task_event_seq<e.task_event_seq AND earlier.status!='succeeded')
                    ORDER BY e.rowid LIMIT 1""", (consumer_id, stamp)).fetchone()
                if row is None:
                    return None
                chosen = (row["id"], row["inbox_attempts"], row["inbox_max"])
                event = _event_from_row(row)
                handler(con, event)
                con.execute("""UPDATE consumer_inbox SET status='succeeded',attempts=attempts+1,
                    processed_at=?,last_error=NULL WHERE consumer_id=? AND event_id=?""",
                            (stamp, consumer_id, row["id"]))
                con.execute("""INSERT INTO consumer_checkpoints(consumer_id,last_event_id,updated_at)
                    VALUES(?,?,?) ON CONFLICT(consumer_id) DO UPDATE SET
                    last_event_id=excluded.last_event_id,updated_at=excluded.updated_at""",
                            (consumer_id, row["id"], stamp))
                return row["id"]
        except Exception as exc:
            if chosen is None:
                raise
            event_id, prior_attempts, maximum = chosen
            attempts = prior_attempts + 1
            status = "failed" if attempts >= maximum else "pending"
            with self.connection_factory() as con:
                con.execute("""UPDATE consumer_inbox SET status=?,attempts=?,last_error=?,next_attempt_at=?
                    WHERE consumer_id=? AND event_id=? AND status='pending'""",
                    (status, attempts, str(exc)[:500], iso((now or utc_now()) + timedelta(seconds=2 ** attempts)),
                     consumer_id, event_id))
            return None
