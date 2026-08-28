from __future__ import annotations

import argparse
import json
from pathlib import Path

from .kit import (
    backup,
    install,
    model_store_quota,
    model_store_register,
    plan,
    rollback,
    uninstall,
    upgrade,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HLAIR prefix installer (no systemd enable)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_prefix(p: argparse.ArgumentParser) -> None:
        p.add_argument("--prefix", required=True)
        p.add_argument("--source-root", default=".")

    p_plan = sub.add_parser("plan")
    add_prefix(p_plan)
    p_inst = sub.add_parser("install")
    add_prefix(p_inst)
    p_up = sub.add_parser("upgrade")
    add_prefix(p_up)
    p_un = sub.add_parser("uninstall")
    add_prefix(p_un)
    p_un.add_argument("--purge", action="store_true")
    p_un.add_argument("--keep-models", action="store_true", default=True)
    p_bak = sub.add_parser("backup")
    add_prefix(p_bak)
    p_rb = sub.add_parser("rollback")
    add_prefix(p_rb)
    p_reg = sub.add_parser("model-register")
    add_prefix(p_reg)
    p_reg.add_argument("--file", required=True)
    p_reg.add_argument("--id", required=True)
    p_q = sub.add_parser("model-quota")
    add_prefix(p_q)

    args = parser.parse_args(argv)
    source = Path(getattr(args, "source_root", ".")).resolve()
    prefix = Path(args.prefix)
    if args.cmd == "plan":
        print(json.dumps(plan(source, prefix), indent=2))
    elif args.cmd == "install":
        print(json.dumps(install(source, prefix), indent=2))
    elif args.cmd == "upgrade":
        print(json.dumps(upgrade(source, prefix), indent=2))
    elif args.cmd == "uninstall":
        uninstall(prefix, keep_models=not args.purge, purge=args.purge)
    elif args.cmd == "backup":
        print(backup(prefix))
    elif args.cmd == "rollback":
        print(json.dumps(rollback(prefix), indent=2))
    elif args.cmd == "model-register":
        print(
            json.dumps(
                model_store_register(prefix, Path(args.file), args.id),
                indent=2,
            )
        )
    elif args.cmd == "model-quota":
        print(json.dumps(model_store_quota(prefix), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
