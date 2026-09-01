#!/usr/bin/env python3
"""Fail closed on checkpoint gaps, forks, or alternate released histories."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from verify_subject import load


TAG = re.compile(
    r"^checkpoint-([0-9a-f-]{36})-(\d{6})-([0-9a-f]{64})$"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--release-list", type=Path, required=True)
    parser.add_argument("--tag-output", type=Path, required=True)
    args = parser.parse_args()
    subject = load(args.subject)
    if subject.get("kind") not in {"pre_dispatch", "post_pair", "pause", "closeout"}:
        raise ValueError("checkpoint kind is invalid")
    sequence = subject.get("sequence")
    scope_id = str(subject.get("campaign_scope_id", ""))
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("checkpoint sequence is invalid")
    releases = json.loads(args.release_list.read_text(encoding="utf-8"))
    released: dict[int, str] = {}
    for item in releases:
        match = TAG.fullmatch(str(item.get("tagName", "")))
        if match is None or match.group(1) != scope_id:
            continue
        index = int(match.group(2))
        if index in released:
            raise ValueError("multiple released histories exist for one sequence")
        released[index] = match.group(3)
    if any(index >= sequence for index in released):
        raise ValueError("checkpoint sequence is stale or already forked")
    previous = subject.get("previous_checkpoint_sha256")
    if sequence == 0:
        if previous is not None or released:
            raise ValueError("checkpoint genesis conflicts with released history")
    elif released.get(sequence - 1) != previous or len(released) != sequence:
        raise ValueError("checkpoint predecessor/release history mismatch")
    tag = f"checkpoint-{scope_id}-{sequence:06d}-{subject['record_sha256']}"
    args.tag_output.write_text(tag + "\n", encoding="ascii")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
