#!/usr/bin/env python3
"""Create the public ExternalAnchorReceipt from a verified Sigstore bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verify_subject import canonical, domain_hash, load


SUBJECT_TYPES = {
    "CampaignKeyCertificate",
    "CompletenessCertificate",
    "DisclosureReceipt",
    "DisclosureRequest",
    "EvaluationDeclaration",
    "EvidenceCheckpoint",
    "EvidenceReleaseManifest",
    "PairIntent",
}
REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject-type", required=True)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow-identity", required=True)
    parser.add_argument("--workflow-commit-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.subject_type not in SUBJECT_TYPES:
        raise ValueError("unsupported externally anchored subject type")
    if REPOSITORY_RE.fullmatch(args.repository) is None:
        raise ValueError("repository identity is invalid")
    expected_identity = (
        f"https://github.com/{args.repository}/.github/workflows/anchor.yml"
        "@refs/heads/main"
    )
    if args.workflow_identity != expected_identity:
        raise ValueError("workflow identity is invalid")
    subject = load(args.subject)
    subject_sha256 = subject.get("record_sha256")
    if (
        not isinstance(subject_sha256, str)
        or len(subject_sha256) != 64
        or any(character not in "0123456789abcdef" for character in subject_sha256)
    ):
        raise ValueError("subject digest is invalid")
    bundle_bytes = args.bundle.read_bytes()
    bundle: dict[str, Any] = json.loads(bundle_bytes)
    entries = bundle.get("verificationMaterial", {}).get("tlogEntries", [])
    if not isinstance(entries, list) or len(entries) != 1:
        raise ValueError("Sigstore bundle must contain exactly one transparency entry")
    entry = entries[0]
    proof = entry.get("inclusionProof")
    if not isinstance(proof, dict) or not proof:
        raise ValueError("Sigstore bundle lacks a Rekor inclusion proof")
    raw_log_index = entry["logIndex"]
    raw_integrated_seconds = entry["integratedTime"]
    if isinstance(raw_log_index, bool) or isinstance(raw_integrated_seconds, bool):
        raise ValueError("Sigstore transparency identity is invalid")
    log_index = int(raw_log_index)
    integrated_seconds = int(raw_integrated_seconds)
    if log_index < 0 or integrated_seconds < 0:
        raise ValueError("Sigstore transparency identity is invalid")
    if (
        len(args.workflow_commit_sha) != 40
        or any(
            character not in "0123456789abcdef"
            for character in args.workflow_commit_sha
        )
    ):
        raise ValueError("workflow commit SHA is invalid")
    integrated = datetime.fromtimestamp(
        integrated_seconds, tz=timezone.utc
    ).isoformat(timespec="seconds").replace("+00:00", "Z")
    body = {
        "schema_version": "1.0",
        "anchor_kind": "github_sigstore_rekor",
        "repository": args.repository,
        "workflow_identity": args.workflow_identity,
        "workflow_commit_sha": args.workflow_commit_sha,
        "subject_type": args.subject_type,
        "subject_sha256": subject_sha256,
        "integrated_time_utc": integrated,
        "log_index": log_index,
        "inclusion_proof_sha256": hashlib.sha256(canonical(proof)).hexdigest(),
        "offline_bundle_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "verified_external": True,
    }
    receipt = {
        **body,
        "record_sha256": domain_hash(
            "consequa.evaluation.ExternalAnchorReceipt.v1", body
        ),
    }
    data = canonical(receipt) + b"\n"
    descriptor = os.open(
        args.output,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
        0o600,
    )
    try:
        written = 0
        while written < len(data):
            count = os.write(descriptor, data[written:])
            if count <= 0:
                raise OSError("anchor receipt write made no progress")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
