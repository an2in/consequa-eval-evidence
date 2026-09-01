#!/usr/bin/env python3
"""Fail closed on unsafe public-ledger repository configuration."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


FULL_SHA_ACTION = re.compile(
    r"^\s*uses:\s*[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}\s*$"
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    workflows = sorted((root / ".github" / "workflows").glob("*.yml"))
    if not workflows:
        raise ValueError("ledger contains no trusted workflows")
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        if "pull_request_target:" in text or "permissions: write-all" in text:
            raise ValueError(f"unsafe workflow trigger or permissions: {workflow.name}")
        for line in text.splitlines():
            if "uses:" in line and not FULL_SHA_ACTION.fullmatch(line):
                raise ValueError(
                    f"workflow action is not pinned by full SHA: {workflow.name}: {line}"
                )
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    tracked = completed.stdout.splitlines()
    if any("__pycache__" in path or path.endswith((".pyc", ".pyo")) for path in tracked):
        raise ValueError("generated Python bytecode is tracked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
