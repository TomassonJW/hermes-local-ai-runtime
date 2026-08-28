"""Run the G-05 control plane on its configured loopback address."""

from __future__ import annotations

import argparse
import os

import uvicorn

from .app import create_app
from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(prog="hermes-local-ai-runtime")
    parser.add_argument(
        "--config",
        default=os.environ.get("HERMES_LOCAL_AI_CONFIG"),
        help="runtime YAML (or HERMES_LOCAL_AI_CONFIG)",
    )
    args = parser.parse_args()
    if not args.config:
        parser.error("--config or HERMES_LOCAL_AI_CONFIG is required")
    config = load_config(args.config)
    app = create_app(config)
    uvicorn.run(
        app,
        host=config.listen_host,
        port=config.listen_port,
        access_log=False,
        server_header=False,
    )


if __name__ == "__main__":
    main()
