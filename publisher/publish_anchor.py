#!/usr/bin/env python3
"""Publish one signed Consequa subject and return its verified anchor receipt."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

VERIFIER = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER))
from verify_subject import canonical, domain_hash, load  # noqa: E402


def run(arguments: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({arguments[0]}): {completed.stderr[:1000]}"
        )
    return completed.stdout.strip()


def validate_receipt(
    receipt: dict[str, Any], *, repository: str, subject_type: str, digest: str,
    workflow_identity: str, bundle: bytes,
) -> None:
    fields = {
        "schema_version", "anchor_kind", "repository", "workflow_identity",
        "workflow_commit_sha",
        "subject_type", "subject_sha256", "integrated_time_utc", "log_index",
        "inclusion_proof_sha256", "offline_bundle_sha256", "verified_external",
        "record_sha256",
    }
    if set(receipt) != fields:
        raise ValueError("anchor receipt fields mismatch")
    if (
        receipt["schema_version"] != "1.0"
        or receipt["anchor_kind"] != "github_sigstore_rekor"
        or receipt["repository"] != repository
        or receipt["workflow_identity"] != workflow_identity
        or receipt["subject_type"] != subject_type
        or receipt["subject_sha256"] != digest
        or receipt["verified_external"] is not True
        or receipt["offline_bundle_sha256"] != hashlib.sha256(bundle).hexdigest()
    ):
        raise ValueError("anchor receipt identity mismatch")
    workflow_commit_sha = receipt["workflow_commit_sha"]
    if (
        not isinstance(workflow_commit_sha, str)
        or len(workflow_commit_sha) != 40
        or any(
            character not in "0123456789abcdef"
            for character in workflow_commit_sha
        )
    ):
        raise ValueError("anchor receipt workflow commit is invalid")
    body = {key: value for key, value in receipt.items() if key != "record_sha256"}
    if receipt["record_sha256"] != domain_hash(
        "consequa.evaluation.ExternalAnchorReceipt.v1", body
    ):
        raise ValueError("anchor receipt digest mismatch")


def immutable_release_exists(repository: str, tag: str) -> bool:
    completed = subprocess.run(
        [
            "gh", "release", "view", tag, "--repo", repository,
            "--json", "isImmutable", "--jq", ".isImmutable",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        text=True,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default="an2in/consequa-eval-evidence")
    parser.add_argument("--subject-type", required=True)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--related-intent", type=Path)
    parser.add_argument("--related-intent-signature", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    args = parser.parse_args()
    if args.timeout_seconds < 30 or args.timeout_seconds > 900:
        raise ValueError("timeout must be between 30 and 900 seconds")
    if (args.related_intent is None) != (args.related_intent_signature is None):
        raise ValueError("related PairIntent and signature must be supplied together")
    if shutil.which("gh") is None or shutil.which("cosign") is None:
        raise RuntimeError("publisher requires authenticated gh and pinned cosign")
    subject = load(args.subject)
    digest = str(subject["record_sha256"])
    scope_id = str(subject.get("campaign_scope_id", ""))
    if len(scope_id) != 36:
        raise ValueError("campaign scope identity is invalid")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("subject digest is invalid")
    if args.subject_type == "EvidenceCheckpoint":
        sequence = subject.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("checkpoint sequence is invalid")
        if args.related_intent is None:
            raise ValueError("checkpoint publication requires its PairIntent")
        tag = f"checkpoint-{scope_id}-{sequence:06d}-{digest}"
    else:
        tag = f"root-{scope_id}-{digest}"
    with tempfile.TemporaryDirectory(prefix="consequa-anchor-") as temporary:
        workspace = Path(temporary)
        if not immutable_release_exists(args.repository, tag):
            checkout = workspace / "ledger"
            run(["gh", "repo", "clone", args.repository, str(checkout), "--", "--depth=1"])
            candidate_branch = f"anchor/{digest}-{time.time_ns()}"
            run(["git", "checkout", "-b", candidate_branch], cwd=checkout)
            pending = checkout / "pending" / digest
            pending.mkdir(parents=True, mode=0o700)
            shutil.copyfile(args.subject, pending / "subject.json")
            shutil.copyfile(args.signature, pending / "signature.json")
            if args.related_intent is not None:
                shutil.copyfile(args.related_intent, pending / "pair-intent.json")
                shutil.copyfile(
                    args.related_intent_signature,
                    pending / "pair-intent-signature.json",
                )
            run(["git", "add", "--", f"pending/{digest}"], cwd=checkout)
            run(
                [
                    "git", "-c", "user.name=Consequa Evidence Operator",
                    "-c", "user.email=evidence@users.noreply.github.com",
                    "commit", "-m", f"anchor: {args.subject_type} {digest}",
                ],
                cwd=checkout,
            )
            commit = run(["git", "rev-parse", "HEAD"], cwd=checkout)
            run(
                ["git", "push", "origin", f"HEAD:refs/heads/{candidate_branch}"],
                cwd=checkout,
            )
            run(
                [
                    "gh", "workflow", "run", "anchor.yml", "--repo", args.repository,
                    "--ref", "main", "-f", f"candidate_commit={commit}",
                    "-f", f"subject_type={args.subject_type}",
                    "-f", f"subject_sha256={digest}",
                ]
            )
        deadline = time.monotonic() + args.timeout_seconds
        while time.monotonic() < deadline:
            if immutable_release_exists(args.repository, tag):
                break
            time.sleep(5)
        else:
            raise RuntimeError("timed out waiting for immutable anchor release")
        release = workspace / "release"
        run(["gh", "release", "download", tag, "--repo", args.repository, "--dir", str(release)])
        downloaded_subject = release / "subject.json"
        if downloaded_subject.read_bytes() != args.subject.read_bytes():
            raise ValueError("released subject bytes differ from local subject")
        identity = (
            f"https://github.com/{args.repository}/.github/workflows/anchor.yml"
            "@refs/heads/main"
        )
        bundle = (release / "subject.sigstore.json").read_bytes()
        receipt = load(release / "anchor-receipt.json")
        validate_receipt(
            receipt,
            repository=args.repository,
            subject_type=args.subject_type,
            digest=digest,
            workflow_identity=identity,
            bundle=bundle,
        )
        run(
            [
                "cosign", "verify-blob", "--bundle",
                str(release / "subject.sigstore.json"),
                "--certificate-identity", identity,
                "--certificate-github-workflow-sha",
                receipt["workflow_commit_sha"],
                "--certificate-oidc-issuer",
                "https://token.actions.githubusercontent.com",
                str(downloaded_subject),
            ]
        )
        attestation_deadline = time.monotonic() + min(args.timeout_seconds, 120)
        while True:
            try:
                release_attestation = run(
                    [
                        "gh", "release", "verify", tag, "--repo", args.repository,
                        "--format", "json",
                    ]
                ).encode("utf-8") + b"\n"
                break
            except RuntimeError:
                if time.monotonic() >= attestation_deadline:
                    raise RuntimeError(
                        "immutable release attestation did not become verifiable"
                    ) from None
                time.sleep(5)
        trusted_root = run(["gh", "attestation", "trusted-root"]).encode("utf-8") + b"\n"
        cosign_trusted_root = run(
            ["cosign", "trusted-root", "create", "--with-default-services"]
        ).encode("utf-8") + b"\n"
        support = args.subject.resolve().parents[1] / "anchor-bundles" / digest
        support.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name, data in (
            ("subject.sigstore.json", bundle),
            ("github-release-attestation.json", release_attestation),
            ("trusted-root.jsonl", trusted_root),
            ("cosign-trusted-root.json", cosign_trusted_root),
        ):
            target = support / name
            if target.exists():
                if target.read_bytes() != data:
                    raise ValueError("existing anchor support bundle drifted")
                continue
            descriptor = os.open(
                target,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
                0o600,
            )
            try:
                written = 0
                while written < len(data):
                    count = os.write(descriptor, data[written:])
                    if count <= 0:
                        raise OSError("anchor support bundle write made no progress")
                    written += count
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        output = canonical(receipt) + b"\n"
        written = 0
        while written < len(output):
            count = os.write(1, output[written:])
            if count <= 0:
                raise OSError("anchor receipt stdout write made no progress")
            written += count
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
