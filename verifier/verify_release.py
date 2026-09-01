#!/usr/bin/env python3
"""Offline verifier for one packaged Consequa evidence release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from verify_subject import canonical, load, verify


RELEASE_FIELDS = {
    "schema_version",
    "campaign_scope_id",
    "release_kind",
    "evaluation_declaration_sha256",
    "public_files",
    "auditor_plaintext_tree_sha256",
    "auditor_encryption",
    "auditor_ciphertext_chunks",
    "checkpoint_head_sha256",
    "completeness_certificate_sha256",
    "operator_signature_sha256",
    "sigstore_bundle_sha256",
    "verifier_sha256",
    "created_at_utc",
    "record_sha256",
}

PUBLIC_SECRET_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(rb"(?i)authorization\s*[:=]\s*bearer\s+[^\s,;]+"),
    re.compile(
        rb"(?i)(?:refresh[_-]?token|access[_-]?token|api[_-]?key|password)\s*[:=]"
    ),
    re.compile(rb'(?i)"(?:email|account_id|accountid|account_email|user_email)"\s*:'),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or ".." in path.parts
        or str(path) != raw
        or "\0" in raw
    ):
        raise ValueError(f"unsafe evidence path: {raw!r}")
    return path


def manifest(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"evidence root is not a real directory: {root}")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        safe_path(relative)
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"evidence tree contains a symlink: {relative}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"evidence tree contains a special/hard-linked file: {relative}")
        data = path.read_bytes()
        files.append({"path": relative, "sha256": sha256(data), "size": len(data)})
    return files


def validate_file_list(raw: Any, *, name: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{name} is not a non-empty array")
    result: list[dict[str, Any]] = []
    paths: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "size"}:
            raise ValueError(f"{name} entry fields mismatch")
        path = str(item["path"])
        safe_path(path)
        digest = item["sha256"]
        size = item["size"]
        if path in paths:
            raise ValueError(f"{name} contains a duplicate path")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
        ):
            raise ValueError(f"{name} entry identity is invalid")
        paths.add(path)
        result.append({"path": path, "sha256": digest, "size": size})
    return result


def record_digests(root: Path) -> set[str]:
    digests: set[str] = set()
    for path in root.rglob("*.json"):
        try:
            value = load(path)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            continue
        digest = value.get("record_sha256")
        if isinstance(digest, str) and len(digest) == 64:
            digests.add(digest)
    return digests


def unique_public_file_by_sha256(root: Path, digest: str) -> Path:
    matches = [
        root / item["path"]
        for item in manifest(root)
        if item["sha256"] == digest
    ]
    if len(matches) != 1:
        raise ValueError("public tier does not resolve a unique committed file")
    return matches[0]


def unique_public_record(root: Path, digest: str) -> Path:
    matches: list[Path] = []
    for path in root.rglob("*.json"):
        try:
            value = load(path)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            continue
        if value.get("record_sha256") == digest:
            matches.append(path)
    if len(matches) != 1:
        raise ValueError("public tier does not resolve a unique committed record")
    return matches[0]


def verify_public_tier(root: Path, expected: list[dict[str, Any]]) -> None:
    actual = manifest(root)
    if actual != expected:
        raise ValueError("public evidence files differ from the release manifest")
    for item in actual:
        data = (root / item["path"]).read_bytes()
        if any(pattern.search(data) for pattern in PUBLIC_SECRET_PATTERNS):
            raise ValueError(f"public evidence secret scan failed: {item['path']}")


def verify_chunks(root: Path, expected: list[dict[str, Any]]) -> None:
    actual = manifest(root)
    if actual != expected:
        raise ValueError("auditor ciphertext chunks differ from the release manifest")


def verify_encryption(raw: Any, root: Path, chunks: list[dict[str, Any]]) -> None:
    fields = {
        "algorithm",
        "auditor_recipient_fingerprint",
        "plaintext_sha256",
        "ciphertext_sha256",
        "ciphertext_size",
    }
    if not isinstance(raw, dict) or set(raw) != fields:
        raise ValueError("auditor_encryption fields mismatch")
    if raw["algorithm"] != "openpgp_hidden_recipient_v1":
        raise ValueError("auditor encryption algorithm is unsupported")
    fingerprint = raw["auditor_recipient_fingerprint"]
    if (
        not isinstance(fingerprint, str)
        or len(fingerprint) < 40
        or any(character not in "0123456789ABCDEF" for character in fingerprint)
    ):
        raise ValueError("auditor encryption fingerprint is invalid")
    for field in ("plaintext_sha256", "ciphertext_sha256"):
        digest = raw[field]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(f"auditor encryption {field} is invalid")
    size = raw["ciphertext_size"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("auditor encryption ciphertext_size is invalid")
    digest = hashlib.sha256()
    observed_size = 0
    for item in chunks:
        data = (root / item["path"]).read_bytes()
        digest.update(data)
        observed_size += len(data)
    if observed_size != size or digest.hexdigest() != raw["ciphertext_sha256"]:
        raise ValueError("auditor ciphertext reconstruction differs from commitment")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--release-signature", type=Path, required=True)
    parser.add_argument("--operator-public-key", type=Path, required=True)
    parser.add_argument("--verifier", type=Path)
    parser.add_argument("--auditor-root", type=Path)
    parser.add_argument("--cosign", type=Path)
    parser.add_argument("--sigstore-trusted-root", type=Path)
    parser.add_argument("--certificate-identity")
    parser.add_argument(
        "--certificate-oidc-issuer",
        default="https://token.actions.githubusercontent.com",
    )
    parser.add_argument("--synthetic-test-only", action="store_true")
    args = parser.parse_args()

    bundle = args.bundle_root.resolve()
    release_path = bundle / "evidence-release-manifest.json"
    release = load(release_path)
    if set(release) != RELEASE_FIELDS:
        raise ValueError("EvidenceReleaseManifest fields mismatch")
    verify(
        "EvidenceReleaseManifest",
        release_path,
        args.release_signature,
        args.operator_public_key,
    )
    if release["schema_version"] != "1.0" or release["release_kind"] not in {
        "precommit",
        "final",
    }:
        raise ValueError("EvidenceReleaseManifest version or kind is invalid")

    public_files = validate_file_list(release["public_files"], name="public_files")
    chunk_files = validate_file_list(
        release["auditor_ciphertext_chunks"],
        name="auditor_ciphertext_chunks",
    )
    verify_public_tier(bundle / "public", public_files)
    verify_chunks(bundle / "ciphertext-chunks", chunk_files)
    verify_encryption(
        release["auditor_encryption"], bundle / "ciphertext-chunks", chunk_files
    )
    public_hashes = {item["sha256"] for item in public_files}
    for field in ("operator_signature_sha256", "sigstore_bundle_sha256"):
        if release[field] not in public_hashes:
            raise ValueError(f"{field} is not present in the public tier")

    public_records = record_digests(bundle / "public")
    if release["evaluation_declaration_sha256"] not in public_records:
        raise ValueError("public tier omits the declared EvaluationDeclaration")
    if release["release_kind"] == "final":
        for field in ("checkpoint_head_sha256", "completeness_certificate_sha256"):
            if release[field] not in public_records:
                raise ValueError(f"public tier omits the final {field}")

    if args.verifier is not None:
        if sha256(args.verifier.read_bytes()) != release["verifier_sha256"]:
            raise ValueError("offline verifier digest mismatch")
    if args.auditor_root is not None:
        auditor_files = manifest(args.auditor_root.resolve())
        tree_sha256 = sha256(canonical(auditor_files))
        if tree_sha256 != release["auditor_plaintext_tree_sha256"]:
            raise ValueError("decrypted auditor evidence tree differs from commitment")

    sigstore_verified = False
    if not args.synthetic_test_only:
        if (
            args.cosign is None
            or args.sigstore_trusted_root is None
            or args.certificate_identity is None
        ):
            raise ValueError(
                "offline Sigstore verification requires cosign, trusted root, and identity"
            )
        cosign = args.cosign.resolve()
        if not cosign.is_file() or not os.access(cosign, os.X_OK):
            raise ValueError("cosign must be an executable regular file")
        trusted_root = args.sigstore_trusted_root.resolve()
        if not trusted_root.is_file() or trusted_root.is_symlink():
            raise ValueError("Sigstore trusted root must be a regular file")
        sigstore_bundle = unique_public_file_by_sha256(
            bundle / "public", release["sigstore_bundle_sha256"]
        )
        sigstore_subject = unique_public_record(
            bundle / "public", release["evaluation_declaration_sha256"]
        )
        completed = subprocess.run(
            [
                str(cosign),
                "verify-blob",
                "--trusted-root",
                str(trusted_root),
                "--bundle",
                str(sigstore_bundle),
                "--certificate-identity",
                args.certificate_identity,
                "--certificate-oidc-issuer",
                args.certificate_oidc_issuer,
                str(sigstore_subject),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError("offline Sigstore identity/proof verification failed")
        sigstore_verified = True

    print(
        json.dumps(
            {
                "status": "VERIFIED_RELEASE",
                "campaign_scope_id": release["campaign_scope_id"],
                "release_kind": release["release_kind"],
                "release_manifest_sha256": release["record_sha256"],
                "public_file_count": len(public_files),
                "ciphertext_chunk_count": len(chunk_files),
                "auditor_plaintext_verified": args.auditor_root is not None,
                "sigstore_cryptographically_verified": sigstore_verified,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc
