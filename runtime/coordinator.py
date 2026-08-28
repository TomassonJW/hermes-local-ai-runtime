"""Bounded asynchronous job coordinator."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import queue
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass

from . import RUNTIME_VERSION
from .admission import Admission
from .config import RouteConfig, RuntimeConfig
from .store import IdempotencyConflict, JobRow, JobStore
from .workers import WorkerError, run_worker_process, validate_against_schema


@dataclass(frozen=True)
class Submission:
    job: JobRow
    created: bool


class JobCoordinator:
    def __init__(self, config: RuntimeConfig, store: JobStore):
        self.config = config
        self.store = store
        self.admission = Admission(config.budget)
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=config.budget.queue_max)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._mp = multiprocessing.get_context("spawn")
        self._active_lock = threading.Lock()
        self._active_processes: dict[str, multiprocessing.Process] = {}
        self._payload_lock = threading.Lock()
        self._requests: dict[str, dict] = {}
        self._results: OrderedDict[str, dict] = OrderedDict()
        self._result_sizes: dict[str, int] = {}
        self._result_total_bytes = 0
        self.recovered_jobs = 0

    def start(self) -> None:
        self.recovered_jobs = self.store.recover_incomplete()
        worker_count = max(
            1, self.config.budget.heavy_slots + self.config.budget.light_slots
        )
        self._threads = [
            threading.Thread(
                target=self._run,
                name=f"job-coordinator-{index + 1}",
                daemon=True,
            )
            for index in range(worker_count)
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._active_lock:
            active = list(self._active_processes.items())
        for job_id, process in active:
            self.store.request_cancel(job_id)
            self._terminate_process(process)
        for _thread in self._threads:
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                break
        for thread in self._threads:
            thread.join(timeout=5)
        with self._payload_lock:
            self._requests.clear()
            self._results.clear()
            self._result_sizes.clear()
            self._result_total_bytes = 0

    def submit(
        self,
        consumer: str,
        request: dict,
        idempotency_key: str | None,
    ) -> Submission:
        route = self.config.route_for(
            request["capability"], request["capability_version"], request["profile"]
        )
        if route is None:
            raise CapabilityUnavailable
        canonical = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        if len(canonical) > self.config.budget.request_max_bytes:
            raise InputTooLarge("request exceeds the byte limit")
        request_hash = hashlib.sha256(canonical).hexdigest()

        decision = self.admission.try_enqueue()
        if not decision.admitted:
            raise QueueFull(decision.reason, decision.retry_after_seconds)
        try:
            job, created = self.store.create(
                consumer,
                request,
                route.id,
                idempotency_key,
                request_hash,
                status="queued",
            )
        except Exception:
            self.admission.dequeue()
            raise
        if not created:
            self.admission.dequeue()
            return Submission(job, False)
        with self._payload_lock:
            self._requests[job.job_id] = request
        try:
            self._queue.put_nowait(job.job_id)
        except queue.Full as exc:  # Defensive: Admission and queue share the same bound.
            self.admission.dequeue()
            with self._payload_lock:
                self._requests.pop(job.job_id, None)
            self.store.set_status(
                job.job_id,
                "rejected",
                error={"code": "QUEUE_FULL", "message": "queue is full", "retryable": True},
            )
            raise QueueFull("queue is full", 10) from exc
        return Submission(job, True)

    def result(self, job_id: str) -> dict | None:
        with self._payload_lock:
            result = self._results.get(job_id)
            if result is not None:
                self._results.move_to_end(job_id)
            return result

    def wait(self, job_id: str, timeout_s: float) -> JobRow | None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            row = self.store.get(job_id)
            if row is None or row.status in {
                "succeeded",
                "failed",
                "cancelled",
                "expired",
                "rejected",
            }:
                return row
            time.sleep(0.01)
        return self.store.get(job_id)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                job_id = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if job_id is None:
                break
            try:
                self._execute(job_id)
            finally:
                self._queue.task_done()

    def _execute(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job is None or job.status == "cancelled" or job.cancel_requested:
            self.admission.dequeue()
            if job and job.status != "cancelled":
                self.store.set_status(job_id, "cancelled")
            with self._payload_lock:
                self._requests.pop(job_id, None)
            return
        with self._payload_lock:
            request = self._requests.get(job_id)
        if request is None:
            self.admission.dequeue()
            self.store.set_status(
                job_id,
                "failed",
                error={
                    "code": "WORKER_CRASHED",
                    "message": "volatile request payload is unavailable",
                    "retryable": True,
                },
            )
            return
        route = next((r for r in self.config.routes if r.id == job.route_id), None)
        if route is None:
            self.admission.dequeue()
            with self._payload_lock:
                self._requests.pop(job_id, None)
            self.store.set_status(
                job_id,
                "failed",
                error={
                    "code": "CAPABILITY_UNAVAILABLE",
                    "message": "route disappeared before execution",
                    "retryable": False,
                },
            )
            return

        decision = self.admission.try_lease(route)
        if decision.code == "SLOT_BUSY":
            # Keep the admission queue count reserved while rotating this
            # accepted job to the tail. New submissions cannot steal its bound.
            self._queue.put(job_id)
            time.sleep(0.01)
            return
        self.admission.dequeue()
        if not decision.admitted:
            with self._payload_lock:
                self._requests.pop(job_id, None)
            self.store.set_status(
                job_id,
                "rejected",
                error={
                    "code": decision.code,
                    "message": decision.reason,
                    "retryable": True,
                    "retry_after_seconds": decision.retry_after_seconds,
                },
            )
            return

        started = time.monotonic()
        queued_ms = max(0, round((time.time() - job.created_at) * 1000))
        self.store.set_status(job_id, "running")
        try:
            output = self._execute_isolated(route, job, request)
            inference_ms = round((time.monotonic() - started) * 1000)
            if self.store.cancel_requested(job_id):
                self.store.set_status(job_id, "cancelled")
                return
            validation_started = time.monotonic()
            schema = request.get("output_schema")
            if schema:
                validated = output.get("data", output)
                violations = validate_against_schema(validated, schema)
                if violations:
                    raise WorkerError(
                        "OUTPUT_SCHEMA_FAILED", "; ".join(violations[:5]), True
                    )
            validation_ms = round((time.monotonic() - validation_started) * 1000)
            total_ms = max(
                queued_ms + inference_ms + validation_ms,
                round((time.time() - job.created_at) * 1000),
            )
            provenance = self._provenance(route, job)
            warnings = []
            if route.worker == "openai-upstream":
                warnings.append(
                    {
                        "code": "TIMING_AGGREGATED",
                        "message": "upstream model load time is included in inference_ms",
                    }
                )
            immutable_result = {
                "result": output,
                "evidence": [],
                "warnings": warnings,
                "review_required": False,
                "provenance": provenance,
            }
            result_size = len(
                json.dumps(immutable_result, sort_keys=True, separators=(",", ":")).encode()
            )
            if result_size > min(
                self.config.budget.result_max_bytes,
                self.config.budget.result_store_max_bytes,
            ):
                raise WorkerError("OUTPUT_TOO_LARGE", "result exceeds the byte limit", False)
            timing = {
                "queued_ms": queued_ms,
                "load_ms": 0,
                "inference_ms": inference_ms,
                "validation_ms": validation_ms,
                "total_ms": total_ms,
            }
            with self._payload_lock:
                self._results[job_id] = immutable_result
                self._result_sizes[job_id] = result_size
                self._result_total_bytes += result_size
                self._results.move_to_end(job_id)
                while (
                    len(self._results) > self.config.budget.result_max_count
                    or self._result_total_bytes
                    > self.config.budget.result_store_max_bytes
                ):
                    evicted_id, _ = self._results.popitem(last=False)
                    self._result_total_bytes -= self._result_sizes.pop(evicted_id)
            if not self.store.complete_success_if_not_cancelled(job_id, timing):
                with self._payload_lock:
                    if self._results.pop(job_id, None) is not None:
                        self._result_total_bytes -= self._result_sizes.pop(job_id)
        except JobCancelled:
            self.store.set_status(job_id, "cancelled")
        except WorkerError as exc:
            total_ms = round((time.monotonic() - started) * 1000)
            self.store.complete_failure_if_not_cancelled(
                job_id,
                {"code": exc.code, "message": str(exc), "retryable": exc.retryable},
                {"total_ms": total_ms},
            )
        except Exception:
            total_ms = round((time.monotonic() - started) * 1000)
            self.store.complete_failure_if_not_cancelled(
                job_id,
                {
                    "code": "INTERNAL_ERROR",
                    "message": "worker failed without exposing payload details",
                    "retryable": False,
                },
                {"total_ms": total_ms},
            )
        finally:
            with self._payload_lock:
                self._requests.pop(job_id, None)
            self.admission.release(route)

    def _execute_isolated(self, route: RouteConfig, job: JobRow, request: dict) -> dict:
        """Execute one adapter in a terminable child process. Closing the
        process also closes an in-flight upstream HTTP connection, so a real
        cancellation does not wait for inference completion."""
        if self._stop.is_set():
            self.store.request_cancel(job.job_id)
            raise JobCancelled
        result_queue = self._mp.Queue(maxsize=1)
        process = self._mp.Process(
            target=run_worker_process,
            args=(route, request, result_queue),
            name=f"worker-{job.job_id}",
            daemon=True,
        )
        process.start()
        with self._active_lock:
            self._active_processes[job.job_id] = process
        if self._stop.is_set():
            self.store.request_cancel(job.job_id)
            self._terminate_process(process)
        requested_timeout_ms = (request.get("constraints") or {}).get("timeout_ms")
        effective_timeout_ms = route.timeout_ms
        if isinstance(requested_timeout_ms, int) and not isinstance(
            requested_timeout_ms, bool
        ):
            effective_timeout_ms = min(route.timeout_ms, requested_timeout_ms)
        deadline = time.monotonic() + effective_timeout_ms / 1000
        message: dict | None = None
        try:
            while message is None:
                if self.store.cancel_requested(job.job_id):
                    self._terminate_process(process)
                    raise JobCancelled
                if time.monotonic() >= deadline:
                    self._terminate_process(process)
                    raise WorkerError("TIMEOUT", "worker deadline exceeded", True)
                try:
                    message = result_queue.get(timeout=0.02)
                except queue.Empty:
                    if not process.is_alive():
                        break
            process.join(timeout=0.2)
            if self.store.cancel_requested(job.job_id):
                raise JobCancelled
            if message is None:
                try:
                    message = result_queue.get(timeout=0.5)
                except queue.Empty as exc:
                    raise WorkerError(
                        "WORKER_CRASHED", "worker returned no result", True
                    ) from exc
            if not message.get("ok"):
                raise WorkerError(
                    message.get("code", "WORKER_CRASHED"),
                    message.get("message", "worker failed"),
                    bool(message.get("retryable", True)),
                )
            return message["output"]
        finally:
            if process.is_alive():
                self._terminate_process(process)
            result_queue.close()
            result_queue.join_thread()
            with self._active_lock:
                self._active_processes.pop(job.job_id, None)

    @staticmethod
    def _terminate_process(process: multiprocessing.Process) -> None:
        if process.is_alive():
            process.terminate()
            process.join(timeout=0.5)
        if process.is_alive():
            process.kill()
            process.join(timeout=0.5)

    @staticmethod
    def _provenance(route: RouteConfig, job: JobRow) -> dict:
        return {
            "runtime_version": RUNTIME_VERSION,
            "capability": job.capability,
            "capability_version": route.capability_version,
            "route": route.id,
            "profile": job.profile,
            "engine": route.engine,
            "engine_version": route.engine_version,
            "model_artifacts": list(route.model_artifacts),
            "preset": route.preset,
            "transformations": [],
            "cache": "bypass",
            "hardware_profile": "hermes-cpu-8vcpu-16gib",
        }


class CapabilityUnavailable(RuntimeError):
    pass


class QueueFull(RuntimeError):
    def __init__(self, reason: str, retry_after_seconds: int | None):
        super().__init__(reason)
        self.retry_after_seconds = retry_after_seconds


class InputTooLarge(RuntimeError):
    pass


class JobCancelled(RuntimeError):
    pass


__all__ = [
    "CapabilityUnavailable",
    "IdempotencyConflict",
    "JobCoordinator",
    "InputTooLarge",
    "QueueFull",
    "Submission",
]
