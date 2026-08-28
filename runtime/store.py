"""Durable SQLite metadata only; request and result payloads stay in memory."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 2

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  consumer TEXT NOT NULL,
  capability TEXT NOT NULL,
  capability_version TEXT NOT NULL,
  profile TEXT NOT NULL,
  route_id TEXT,
  status TEXT NOT NULL,
  error_json TEXT,
  idempotency_key TEXT,
  request_hash TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  queued_ms INTEGER,
  load_ms INTEGER,
  inference_ms INTEGER,
  validation_ms INTEGER,
  total_ms INTEGER,
  cancel_requested INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_idem
  ON jobs(consumer, idempotency_key) WHERE idempotency_key IS NOT NULL;
"""

TERMINAL = {"succeeded", "failed", "cancelled", "expired", "rejected"}


@dataclass
class JobRow:
    job_id: str
    consumer: str
    capability: str
    capability_version: str
    profile: str
    route_id: str | None
    status: str
    error: dict | None
    cancel_requested: bool
    timing: dict
    created_at: float


class JobStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._prepare_private_path()
        con = self._connect()
        try:
            with con:
                con.executescript(_SCHEMA)
                legacy_columns = {
                    row[1] for row in con.execute("PRAGMA table_info(jobs)").fetchall()
                }
                if "request_json" in legacy_columns:
                    self._migrate_legacy_schema(con)
                con.execute(
                    "INSERT INTO meta(key, value) VALUES('schema_version', ?)"
                    " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (str(SCHEMA_VERSION),),
                )
            if "request_json" in legacy_columns:
                con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                con.execute("VACUUM")
        finally:
            con.close()
            self._harden_files()

    def _prepare_private_path(self) -> None:
        parent = self._path.parent
        if parent.exists():
            if parent.is_symlink() or not parent.is_dir():
                raise PermissionError("job store parent must be a real directory")
            if stat.S_IMODE(parent.stat().st_mode) & 0o077:
                raise PermissionError("job store parent must not be group/world accessible")
        else:
            parent.mkdir(parents=True, mode=0o700)
        if self._path.exists():
            info = self._path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise PermissionError("job store must be a regular file")
            if stat.S_IMODE(info.st_mode) & 0o077:
                raise PermissionError("job store must not be group/world accessible")
        else:
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(self._path, flags, 0o600)
            os.close(descriptor)

    def _harden_files(self) -> None:
        for candidate in (
            self._path,
            Path(f"{self._path}-wal"),
            Path(f"{self._path}-shm"),
        ):
            if candidate.exists() and not candidate.is_symlink():
                os.chmod(candidate, 0o600)

    @staticmethod
    def _migrate_legacy_schema(con: sqlite3.Connection) -> None:
        con.executescript(
            """
            DROP INDEX IF EXISTS idx_jobs_status;
            DROP INDEX IF EXISTS idx_jobs_idem;
            CREATE TABLE jobs_v2 (
              job_id TEXT PRIMARY KEY,
              consumer TEXT NOT NULL,
              capability TEXT NOT NULL,
              capability_version TEXT NOT NULL,
              profile TEXT NOT NULL,
              route_id TEXT,
              status TEXT NOT NULL,
              error_json TEXT,
              idempotency_key TEXT,
              request_hash TEXT,
              created_at REAL NOT NULL,
              updated_at REAL NOT NULL,
              queued_ms INTEGER,
              load_ms INTEGER,
              inference_ms INTEGER,
              validation_ms INTEGER,
              total_ms INTEGER,
              cancel_requested INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO jobs_v2(
              job_id, consumer, capability, capability_version, profile,
              route_id, status, error_json, idempotency_key, request_hash,
              created_at, updated_at, queued_ms, load_ms, inference_ms,
              validation_ms, total_ms, cancel_requested
            )
            SELECT
              job_id, consumer, capability, capability_version, profile,
              route_id, status, error_json, idempotency_key, request_hash,
              created_at, updated_at, queued_ms, load_ms, inference_ms,
              validation_ms, total_ms, cancel_requested
            FROM jobs;
            DROP TABLE jobs;
            ALTER TABLE jobs_v2 RENAME TO jobs;
            CREATE INDEX idx_jobs_status ON jobs(status);
            CREATE UNIQUE INDEX idx_jobs_idem
              ON jobs(consumer, idempotency_key) WHERE idempotency_key IS NOT NULL;
            """
        )

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    @staticmethod
    def new_job_id() -> str:
        return f"job_{uuid.uuid4().hex[:20]}"

    def create(
        self,
        consumer: str,
        request: dict,
        route_id: str | None,
        idempotency_key: str | None,
        request_hash: str,
        status: str = "queued",
    ) -> tuple[JobRow, bool]:
        """Returns (row, created). With an idempotency key, an existing row for
        the same consumer+key is returned instead (created=False) unless the
        payload hash differs, which raises IdempotencyConflict."""
        now = time.time()
        job_id = self.new_job_id()
        with self._lock:
            con = self._connect()
            try:
                con.execute("BEGIN IMMEDIATE")
                if idempotency_key:
                    cur = con.execute(
                        "SELECT * FROM jobs WHERE consumer=? AND idempotency_key=?",
                        (consumer, idempotency_key),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        if existing["request_hash"] != request_hash:
                            raise IdempotencyConflict(idempotency_key)
                        result = self._row_to_job(existing)
                        con.commit()
                        return result, False
                con.execute(
                    "INSERT INTO jobs(job_id, consumer, capability, capability_version,"
                    " profile, route_id, status, idempotency_key, request_hash,"
                    " created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        job_id,
                        consumer,
                        request["capability"],
                        request["capability_version"],
                        request["profile"],
                        route_id,
                        status,
                        idempotency_key,
                        request_hash,
                        now,
                        now,
                    ),
                )
                inserted = con.execute(
                    "SELECT * FROM jobs WHERE job_id=?", (job_id,)
                ).fetchone()
                con.commit()
                return self._row_to_job(inserted), True
            except BaseException:
                con.rollback()
                raise
            finally:
                con.close()

    def get(self, job_id: str) -> JobRow | None:
        con = self._connect()
        try:
            row = con.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            return self._row_to_job(row) if row is not None else None
        finally:
            con.close()

    def set_status(
        self,
        job_id: str,
        status: str,
        error: dict | None = None,
        timing: dict | None = None,
        route_id: str | None = None,
    ) -> None:
        timing = timing or {}
        values = (
            status,
            time.time(),
            json.dumps(error, ensure_ascii=False) if error is not None else None,
            route_id,
            timing.get("queued_ms"),
            timing.get("load_ms"),
            timing.get("inference_ms"),
            timing.get("validation_ms"),
            timing.get("total_ms"),
            job_id,
        )
        with self._lock:
            con = self._connect()
            try:
                with con:
                    con.execute(
                        """
                        UPDATE jobs SET
                          status=?, updated_at=?,
                          error_json=COALESCE(?, error_json),
                          route_id=COALESCE(?, route_id),
                          queued_ms=COALESCE(?, queued_ms),
                          load_ms=COALESCE(?, load_ms),
                          inference_ms=COALESCE(?, inference_ms),
                          validation_ms=COALESCE(?, validation_ms),
                          total_ms=COALESCE(?, total_ms)
                        WHERE job_id=?
                        """,
                        values,
                    )
            finally:
                con.close()
                self._harden_files()

    def complete_success_if_not_cancelled(self, job_id: str, timing: dict) -> bool:
        """Atomically publish success or cancellation; cancellation wins races."""
        values = (
            time.time(),
            timing.get("queued_ms"),
            timing.get("load_ms"),
            timing.get("inference_ms"),
            timing.get("validation_ms"),
            timing.get("total_ms"),
            job_id,
        )
        with self._lock:
            con = self._connect()
            try:
                with con:
                    con.execute(
                        """
                        UPDATE jobs SET
                          status=CASE WHEN cancel_requested=1 THEN 'cancelled' ELSE 'succeeded' END,
                          updated_at=?,
                          queued_ms=COALESCE(?, queued_ms),
                          load_ms=COALESCE(?, load_ms),
                          inference_ms=COALESCE(?, inference_ms),
                          validation_ms=COALESCE(?, validation_ms),
                          total_ms=COALESCE(?, total_ms)
                        WHERE job_id=? AND status='running'
                        """,
                        values,
                    )
                row = con.execute(
                    "SELECT status FROM jobs WHERE job_id=?", (job_id,)
                ).fetchone()
                return bool(row and row["status"] == "succeeded")
            finally:
                con.close()
                self._harden_files()

    def complete_failure_if_not_cancelled(
        self, job_id: str, error: dict, timing: dict
    ) -> bool:
        """Atomically publish failure or cancellation; cancellation wins races."""
        values = (
            time.time(),
            json.dumps(error, ensure_ascii=False),
            timing.get("queued_ms"),
            timing.get("load_ms"),
            timing.get("inference_ms"),
            timing.get("validation_ms"),
            timing.get("total_ms"),
            job_id,
        )
        with self._lock:
            con = self._connect()
            try:
                with con:
                    con.execute(
                        """
                        UPDATE jobs SET
                          status=CASE WHEN cancel_requested=1 THEN 'cancelled' ELSE 'failed' END,
                          updated_at=?,
                          error_json=CASE WHEN cancel_requested=1 THEN NULL ELSE ? END,
                          queued_ms=COALESCE(?, queued_ms),
                          load_ms=COALESCE(?, load_ms),
                          inference_ms=COALESCE(?, inference_ms),
                          validation_ms=COALESCE(?, validation_ms),
                          total_ms=COALESCE(?, total_ms)
                        WHERE job_id=? AND status='running'
                        """,
                        values,
                    )
                row = con.execute(
                    "SELECT status FROM jobs WHERE job_id=?", (job_id,)
                ).fetchone()
                return bool(row and row["status"] == "failed")
            finally:
                con.close()
                self._harden_files()

    def request_cancel(self, job_id: str) -> str | None:
        """Marks cancellation. Returns current status, or None if unknown."""
        with self._lock:
            con = self._connect()
            try:
                row = con.execute(
                    "SELECT status FROM jobs WHERE job_id=?", (job_id,)
                ).fetchone()
                if row is None:
                    return None
                status = row["status"]
                with con:
                    con.execute(
                        "UPDATE jobs SET cancel_requested=1, updated_at=? WHERE job_id=?",
                        (time.time(), job_id),
                    )
                    if status == "queued":
                        con.execute(
                            "UPDATE jobs SET status='cancelled', updated_at=? WHERE job_id=?",
                            (time.time(), job_id),
                        )
                return status
            finally:
                con.close()

    def cancel_requested(self, job_id: str) -> bool:
        con = self._connect()
        try:
            row = con.execute(
                "SELECT cancel_requested FROM jobs WHERE job_id=?", (job_id,)
            ).fetchone()
            return bool(row and row["cancel_requested"])
        finally:
            con.close()

    def counts_by_status(self) -> dict[str, int]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"
            ).fetchall()
            return {r["status"]: r["n"] for r in rows}
        finally:
            con.close()

    def recover_incomplete(self) -> int:
        """On restart: queued/running jobs from a previous process converge to
        failed with a WORKER_CRASHED-style error (a linked retry is the
        consumer's decision, per the job model)."""
        with self._lock:
            con = self._connect()
            try:
                with con:
                    cur = con.execute(
                        "UPDATE jobs SET status='failed', updated_at=?,"
                        " error_json=?"
                        " WHERE status IN ('queued','running','admitted','loading')",
                        (
                            time.time(),
                            json.dumps(
                                {
                                    "code": "WORKER_CRASHED",
                                    "message": "control plane restarted while the job was active",
                                    "retryable": True,
                                }
                            ),
                        ),
                    )
                return cur.rowcount
            finally:
                con.close()

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> JobRow:
        return JobRow(
            job_id=row["job_id"],
            consumer=row["consumer"],
            capability=row["capability"],
            capability_version=row["capability_version"],
            profile=row["profile"],
            route_id=row["route_id"],
            status=row["status"],
            error=json.loads(row["error_json"]) if row["error_json"] else None,
            cancel_requested=bool(row["cancel_requested"]),
            timing={
                k: row[k]
                for k in ("queued_ms", "load_ms", "inference_ms", "validation_ms", "total_ms")
                if row[k] is not None
            },
            created_at=float(row["created_at"]),
        )


class IdempotencyConflict(RuntimeError):
    pass
