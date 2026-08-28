# Release process

1. Tests and `python3 scripts/validate_bootstrap.py` pass.
2. `python3 -c "from installkit.release import write_checksums; from pathlib import Path; write_checksums(Path('.'))"`
3. Security review in `docs/security-review-g11.md` still matches the tree.
4. Tag only after Thomas's explicit public-release decision. This lot does
   not create a GitHub Release or a production tag by itself.
5. Never attach model weights, `.env`, or request logs to a release.

Source checksums: `packaging/checksums.sha256`.
