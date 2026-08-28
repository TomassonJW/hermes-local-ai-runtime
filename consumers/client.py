"""HTTP-only runtime client. Consumers never import workers or model files."""

from __future__ import annotations

import time
from typing import Any, Protocol


class Transport(Protocol):
    def get(self, url: str, **kwargs: Any) -> Any: ...

    def post(self, url: str, **kwargs: Any) -> Any: ...


POLICY = {
    "data_classification": "internal",
    "cloud_fallback_allowed": False,
    "retention": "none",
}


class CapabilityMissing(RuntimeError):
    pass


class JobFailed(RuntimeError):
    pass


class RuntimeClient:
    def __init__(self, transport: Transport, token: str) -> None:
        self._t = transport
        self._headers = {"Authorization": f"Bearer {token}"}

    def discover(self) -> list[dict]:
        response = self._t.get("/api/v1/capabilities", headers=self._headers)
        if response.status_code != 200:
            raise CapabilityMissing(response.text)
        return list(response.json()["capabilities"])

    def require(self, capability: str, version: str = "1.0.0", profile: str = "balanced") -> dict:
        for item in self.discover():
            if (
                item["id"] == capability
                and item["version"] == version
                and profile in item.get("profiles", [])
                and item.get("status") == "available"
            ):
                return item
        raise CapabilityMissing(f"{capability}@{version}/{profile} is unavailable")

    def invoke(
        self,
        capability: str,
        input_data: dict,
        *,
        version: str = "1.0.0",
        profile: str = "balanced",
        timeout_s: float = 20,
    ) -> dict:
        self.require(capability, version, profile)
        body = {
            "capability": capability,
            "capability_version": version,
            "profile": profile,
            "input": input_data,
            "policy": POLICY,
        }
        submitted = self._t.post("/api/v1/jobs", headers=self._headers, json=body)
        if submitted.status_code not in {200, 202}:
            raise JobFailed(submitted.text)
        job_id = submitted.json()["job_id"]
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            status = self._t.get(f"/api/v1/jobs/{job_id}", headers=self._headers).json()
            if status["status"] == "succeeded":
                payload = self._t.get(f"/api/v1/jobs/{job_id}/result", headers=self._headers)
                if payload.status_code != 200:
                    raise JobFailed(payload.text)
                return payload.json()
            if status["status"] in {"failed", "cancelled", "rejected"}:
                raise JobFailed(f"{capability} {status['status']}")
            time.sleep(0.05)
        raise JobFailed(f"{capability} timed out")

    def upload(self, data: bytes, content_type: str) -> str:
        response = self._t.post(
            "/api/v1/uploads",
            headers={**self._headers, "Content-Type": content_type},
            content=data,
        )
        if response.status_code != 201:
            raise JobFailed(response.text)
        return str(response.json()["upload_id"])
