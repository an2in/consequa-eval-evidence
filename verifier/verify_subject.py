#!/usr/bin/env python3
"""Dependency-free verifier for Consequa public evidence subjects."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


SAFE_INTEGER_MAX = (1 << 53) - 1
DOMAINS = {
    "EvaluationDeclaration": "consequa.evaluation.EvaluationDeclaration.v1",
    "DisclosureRequest": "consequa.evaluation.DisclosureRequest.v1",
    "DisclosureReceipt": "consequa.evaluation.DisclosureReceipt.v1",
    # This is a canonical hash-domain label, not a credential.
    "CampaignKeyCertificate": "consequa.evaluation.CampaignKeyCertificate.v1",  #gitleaks:allow
    "PairIntent": "consequa.evaluation.PairIntent.v1",
    "EvidenceCheckpoint": "consequa.evaluation.EvidenceCheckpoint.v1",
    "CompletenessCertificate": "consequa.evaluation.CompletenessCertificate.v1",
    "EvidenceReleaseManifest": "consequa.evaluation.EvidenceReleaseManifest.v1",
}


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for raw_key, child in pairs:
        key = unicodedata.normalize("NFC", raw_key)
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = child
    return value


def load(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_float=lambda raw: (_ for _ in ()).throw(ValueError(f"float {raw}")),
        parse_constant=lambda raw: (_ for _ in ()).throw(ValueError(raw)),
    )
    if not isinstance(value, dict):
        raise ValueError("JSON subject must be an object")
    return value


def normalize(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = unicodedata.normalize("NFC", value)
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValueError("lone surrogate")
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if not -SAFE_INTEGER_MAX <= value <= SAFE_INTEGER_MAX:
            raise ValueError("unsafe integer")
        return value
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = unicodedata.normalize("NFC", raw_key)
            if key in normalized:
                raise ValueError("NFC-equivalent key")
            normalized[key] = normalize(child)
        return normalized
    raise ValueError("value is outside canonical JSON subset")


def canonical(value: Any) -> bytes:
    value = normalize(value)

    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, int):
            return str(item)
        if isinstance(item, str):
            return json.dumps(item, ensure_ascii=False, allow_nan=False)
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        keys = sorted(item, key=lambda key: key.encode("utf-16-be"))
        return "{" + ",".join(
            encode(key) + ":" + encode(item[key]) for key in keys
        ) + "}"

    return encode(value).encode("utf-8")


def domain_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + canonical(value)).hexdigest()


def verify(subject_type: str, subject: Path, signature: Path, public_key: Path) -> str:
    if subject_type not in DOMAINS:
        raise ValueError("unsupported subject type")
    record = load(subject)
    digest = record.get("record_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("subject record digest is invalid")
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    if domain_hash(DOMAINS[subject_type], body) != digest:
        raise ValueError("subject canonical/domain hash mismatch")
    envelope = load(signature)
    required = {
        "schema_version", "algorithm", "namespace", "key_id", "subject_type",
        "subject_sha256", "signed_at_utc", "signature_base64", "record_sha256",
    }
    if set(envelope) != required:
        raise ValueError("signature envelope fields mismatch")
    if (
        envelope["schema_version"] != "1.0"
        or envelope["algorithm"] != "ed25519"
        or envelope["namespace"] != "consequa-evaluation"
        or envelope["subject_type"] != subject_type
        or envelope["subject_sha256"] != digest
    ):
        raise ValueError("signature envelope subject mismatch")
    envelope_body = {
        key: value for key, value in envelope.items() if key != "record_sha256"
    }
    if domain_hash(
        "consequa.evaluation.Ed25519SignatureEnvelope.v1", envelope_body
    ) != envelope["record_sha256"]:
        raise ValueError("signature envelope hash mismatch")
    material = (
        b"consequa.evaluation.Ed25519Signature.v1\0"
        + subject_type.encode("utf-8")
        + b"\0"
        + bytes.fromhex(digest)
    )
    raw_signature = base64.b64decode(envelope["signature_base64"], validate=True)
    with tempfile.TemporaryDirectory() as temporary:
        material_path = Path(temporary) / "material"
        signature_path = Path(temporary) / "signature"
        material_path.write_bytes(material)
        signature_path.write_bytes(raw_signature)
        completed = subprocess.run(
            [
                "openssl", "pkeyutl", "-verify", "-pubin", "-inkey",
                str(public_key), "-rawin", "-in", str(material_path),
                "-sigfile", str(signature_path),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if completed.returncode != 0:
        raise ValueError("Ed25519 verification failed")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject-type", required=True)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    args = parser.parse_args()
    digest = verify(args.subject_type, args.subject, args.signature, args.public_key)
    print(json.dumps({"status": "VALID", "subject_sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
