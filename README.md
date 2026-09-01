# Consequa evaluation evidence ledger

This directory is the source template for the public
`an2in/consequa-eval-evidence` ledger. It contains no scenario text, raw
transcripts, account identifiers, or OAuth material.

Every release subject is checked against the campaign Ed25519 public key on
the trusted default branch. The workflow then signs the exact canonical JSON
blob using GitHub OIDC and Cosign, requires a Rekor inclusion proof, and
publishes the subject, operator signature, offline Sigstore bundle, and
`ExternalAnchorReceipt` as immutable release assets. Checkpoint releases use
strict sequence tags and reject gaps, duplicate sequence numbers, stale
predecessors, and alternate heads.
Each anchor receipt records the exact trusted workflow commit, and both the
online controller check and offline verifier require the matching signed
GitHub OIDC workflow-SHA claim.

## One-time repository controls

Before any real campaign, an administrator must:

1. Create the public repository with `main` as the default branch.
2. Require pull requests, linear history, signed commits, status checks, and
   conversation resolution on `main`. Human approvals are set to zero because
   no independent reviewer exists; using a second operator-controlled account
   would not create independent assurance.
3. Disable force pushes and branch deletion for `main`.
4. Enable immutable releases and disallow Actions from approving pull
   requests.
5. Limit Actions to trusted actions and require full commit-SHA pinning.
6. Add `campaigns/<campaign-scope-id>/campaign-public.pem`,
   `operator-root-public.pem`, and the operator-root-signed campaign key
   certificate through a reviewed pull request.
7. Record the repository ruleset JSON and immutable-release setting in the
   campaign precommit bundle.

The controller uses `publisher/publish_anchor.py` as an executable command.
It pushes one isolated candidate commit, dispatches the trusted workflow from
`main`, waits for the corresponding immutable release, verifies the Sigstore
bundle and workflow identity locally, then emits only the canonical anchor
receipt on stdout. Any timeout, duplicate release, signature error, missing
proof, or sequence conflict stops the campaign.

The branch containing a candidate is not the trust anchor. The immutable
release, its generated release attestation, the Rekor proof, the offline
Sigstore bundle, and the operator/campaign signature establish the public
record. Candidate branches may be retained for forensic convenience.

## Offline verification

The scripts in `verifier/` use Python's standard library and OpenSSL for the
operator/campaign Ed25519 layer. Cosign verifies the saved Sigstore bundle.
For an air-gapped audit, also archive the current Sigstore trusted root and
GitHub release attestation bundle; do not retrieve a fresh trust root during
the audit and silently substitute it for the archived one.

Run `verifier/verify_release.py` against an unpacked release, its detached
operator-root signature, and the archived operator public key. It validates
the domain-separated manifest signature, exact public allowlist, secret scan,
every encrypted chunk, and the committed verifier binary. After the auditor
decrypts and extracts the raw archive, pass `--auditor-root` to verify the
plaintext tree commitment. It also reconstructs the encrypted stream from
the ordered chunks and verifies its hash, size, hidden-recipient OpenPGP
algorithm, and committed auditor fingerprint. Then run the source-bundled
`consequa-eval evidence verify` command to validate the full intent/checkpoint
chain, completeness certificate, immutable archives, and byte-identical final
aggregate.

For a real release, `verify_release.py` also requires a pinned Cosign binary,
the archived Sigstore trusted root, and the exact expected GitHub workflow
identity; it runs `cosign verify-blob` against the committed declaration and
bundle without retrieving a replacement trust root. The
`--synthetic-test-only` bypass exists solely for the network-free repository
test vector and must never be accepted for campaign evidence.

The encrypted raw staging tree has a fixed minimum layout. Both release kinds
include `source/` (`source.tar`, exact identity, `uv.lock`, SPDX SBOM), full
`manifests/`, `environment/` baseline/vSphere/network evidence,
`evidence/` campaign-key certificate and root signature, and
`mapping/public-to-raw.json`. Calibration precommits and every final release
also include the signed disclosure receipt. A final release additionally
requires the aggregate, completeness certificate, raw results, and non-empty
`ledger/intents`, `ledger/checkpoints`, and `ledger/anchor-bundles` trees.

## Governance boundary

There is no independent human reviewer or co-signing auditor in the campaign
control path. The repository is controlled by the operator. Independent
assurance therefore means after-the-fact cryptographic auditability from
operator-root signatures, immutable release assets, GitHub workflow identity,
and Sigstore/Rekor inclusion proofs. It does not mean that an independent human
witnessed execution, and it cannot exclude runs outside the declared
VM/account/harness boundary.
