"""Resource admission: reserve budget BEFORE any worker activation.

Product invariant: never start and hope the OS resolves overcommit. The
admission decision combines slot leases, queue depth and live MemAvailable
against the configured floor and the route's memory estimate."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from .config import Budget, RouteConfig

HEAVY_CLASSES = {"heavy", "exclusive"}


def mem_available_mib() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) // 1024
    return 0


@dataclass
class AdmissionDecision:
    admitted: bool
    code: str  # admitted | RESOURCE_EXHAUSTED | QUEUE_FULL
    reason: str
    retry_after_seconds: int | None = None


class Admission:
    def __init__(self, budget: Budget):
        self._budget = budget
        self._lock = threading.Lock()
        self._heavy_leases = 0
        self._light_leases = 0
        self._queued = 0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "heavy_leases": self._heavy_leases,
                "light_leases": self._light_leases,
                "queued": self._queued,
                "queue_max": self._budget.queue_max,
                "mem_available_mib": mem_available_mib(),
                "memory_floor_mib": self._budget.memory_floor_available_mib,
            }

    def try_enqueue(self) -> AdmissionDecision:
        with self._lock:
            if self._queued >= self._budget.queue_max:
                return AdmissionDecision(
                    False,
                    "QUEUE_FULL",
                    f"queue is at its bound ({self._budget.queue_max})",
                    retry_after_seconds=10,
                )
            self._queued += 1
            return AdmissionDecision(True, "admitted", "queued")

    def dequeue(self) -> None:
        with self._lock:
            self._queued = max(0, self._queued - 1)

    def try_lease(self, route: RouteConfig) -> AdmissionDecision:
        """Reserve an execution slot + memory headroom for a route."""
        heavy = route.resource_class in HEAVY_CLASSES
        with self._lock:
            if heavy and self._heavy_leases >= self._budget.heavy_slots:
                return AdmissionDecision(
                    False, "SLOT_BUSY", "heavy slot busy", retry_after_seconds=1
                )
            if not heavy and self._light_leases >= self._budget.light_slots:
                return AdmissionDecision(
                    False, "SLOT_BUSY", "light slots busy", retry_after_seconds=1
                )
            available = mem_available_mib()
            needed_floor = self._budget.memory_floor_available_mib + route.memory_estimate_mib
            if available < needed_floor:
                return AdmissionDecision(
                    False,
                    "RESOURCE_EXHAUSTED",
                    (
                        f"admitting would leave under the memory floor: "
                        f"{available} MiB available, need {needed_floor} MiB "
                        f"(floor {self._budget.memory_floor_available_mib}"
                        f" + estimate {route.memory_estimate_mib})"
                    ),
                    retry_after_seconds=30,
                )
            if heavy:
                self._heavy_leases += 1
            else:
                self._light_leases += 1
            return AdmissionDecision(True, "admitted", "lease granted")

    def release(self, route: RouteConfig) -> None:
        heavy = route.resource_class in HEAVY_CLASSES
        with self._lock:
            if heavy:
                self._heavy_leases = max(0, self._heavy_leases - 1)
            else:
                self._light_leases = max(0, self._light_leases - 1)
