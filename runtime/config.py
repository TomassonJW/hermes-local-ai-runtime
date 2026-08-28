"""Configuration: routes, budgets, auth. No secret lives in config files —
tokens are referenced through environment variable names only."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml


@dataclass(frozen=True)
class RouteConfig:
    """One approved route serving a capability."""

    id: str
    capability: str
    capability_version: str
    profiles: tuple[str, ...]
    worker: str  # "echo" | "openai-upstream"
    upstream_base: str | None
    upstream_model: str | None
    engine: str
    engine_version: str
    resource_class: str  # tiny|light|medium|heavy
    memory_estimate_mib: int
    sync_allowed: bool
    timeout_ms: int
    model_artifacts: tuple[str, ...] = ()
    preset: str = "default"
    max_input_chars: int = 32_000
    max_upstream_response_bytes: int = 4 * 1024 * 1024


@dataclass(frozen=True)
class Budget:
    heavy_slots: int = 1
    light_slots: int = 2
    queue_max: int = 8
    memory_floor_available_mib: int = 4096
    hard_memory_mib: int = 10_240
    result_max_count: int = 64
    request_max_bytes: int = 512 * 1024
    result_max_bytes: int = 4 * 1024 * 1024
    result_store_max_bytes: int = 16 * 1024 * 1024


@dataclass(frozen=True)
class TokenConfig:
    name: str
    token: str
    scopes: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeConfig:
    listen_host: str
    listen_port: int
    routes: tuple[RouteConfig, ...]
    budget: Budget
    tokens: tuple[TokenConfig, ...]
    db_path: str
    dev_mode: bool = False

    def route_for(self, capability: str, version: str, profile: str) -> RouteConfig | None:
        for r in self.routes:
            if (
                r.capability == capability
                and r.capability_version == version
                and profile in r.profiles
            ):
                return r
        return None


class ConfigError(RuntimeError):
    pass


def load_config(path: str | Path) -> RuntimeConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")

    listen = raw.get("listen", {})
    host = str(listen.get("host", "127.0.0.1"))
    if host != "127.0.0.1":
        raise ConfigError("only loopback listen is permitted in this phase")

    routes = []
    for r in raw.get("routes", []):
        worker = r["worker"]
        if worker not in {
            "echo",
            "openai-upstream",
            "document-native",
            "document-ocr",
            "document-parse",
            "document-structured",
            "image-embed",
            "object-detect",
        }:
            raise ConfigError(f"unsupported worker kind: {worker}")
        upstream_base = r.get("upstream_base")
        if worker == "openai-upstream":
            parsed = urlparse(str(upstream_base or ""))
            if parsed.scheme != "http" or parsed.hostname not in {
                "127.0.0.1",
                "localhost",
                "::1",
            }:
                raise ConfigError("openai-upstream routes must use a loopback HTTP URL")
        routes.append(
            RouteConfig(
                id=r["id"],
                capability=r["capability"],
                capability_version=str(r["capability_version"]),
                profiles=tuple(r.get("profiles", ["balanced"])),
                worker=worker,
                upstream_base=upstream_base,
                upstream_model=r.get("upstream_model"),
                engine=r.get("engine", "unknown"),
                engine_version=r.get("engine_version", "unknown"),
                resource_class=r.get("resource_class", "light"),
                memory_estimate_mib=int(r.get("memory_estimate_mib", 512)),
                sync_allowed=bool(r.get("sync_allowed", True)),
                timeout_ms=int(r.get("timeout_ms", 60_000)),
                model_artifacts=tuple(r.get("model_artifacts", [])),
                preset=r.get("preset", "default"),
                max_input_chars=int(r.get("max_input_chars", 32_000)),
                max_upstream_response_bytes=max(
                    1024,
                    min(
                        int(r.get("max_upstream_response_bytes", 4 * 1024 * 1024)),
                        32 * 1024 * 1024,
                    ),
                ),
            )
        )

    b = raw.get("budget", {})
    budget = Budget(
        heavy_slots=int(b.get("heavy_slots", 1)),
        light_slots=int(b.get("light_slots", 2)),
        queue_max=int(b.get("queue_max", 8)),
        memory_floor_available_mib=int(b.get("memory_floor_available_mib", 4096)),
        hard_memory_mib=int(b.get("hard_memory_mib", 10_240)),
        result_max_count=max(1, min(int(b.get("result_max_count", 64)), 1024)),
        request_max_bytes=max(
            1024,
            min(int(b.get("request_max_bytes", 512 * 1024)), 8 * 1024 * 1024),
        ),
        result_max_bytes=max(
            1024,
            min(int(b.get("result_max_bytes", 4 * 1024 * 1024)), 32 * 1024 * 1024),
        ),
        result_store_max_bytes=max(
            1024,
            min(
                int(b.get("result_store_max_bytes", 16 * 1024 * 1024)),
                128 * 1024 * 1024,
            ),
        ),
    )

    tokens: list[TokenConfig] = []
    for t in raw.get("auth", {}).get("tokens", []):
        env_name = t["token_env"]
        value = os.environ.get(env_name, "")
        if value:
            tokens.append(
                TokenConfig(name=t["name"], token=value, scopes=tuple(t.get("scopes", [])))
            )
    if len({token.name for token in tokens}) != len(tokens):
        raise ConfigError("resolved auth principal names must be unique")
    if len({token.token for token in tokens}) != len(tokens):
        raise ConfigError("resolved auth token values must be unique")
    dev_mode = bool(raw.get("dev_mode", False))
    if not tokens and not dev_mode:
        raise ConfigError(
            "no auth token resolved from environment and dev_mode is off; refusing to start"
        )

    return RuntimeConfig(
        listen_host=host,
        listen_port=int(listen.get("port", 8090)),
        routes=tuple(routes),
        budget=budget,
        tokens=tuple(tokens),
        db_path=str(raw.get("db_path", "runtime-state.db")),
        dev_mode=dev_mode,
    )
