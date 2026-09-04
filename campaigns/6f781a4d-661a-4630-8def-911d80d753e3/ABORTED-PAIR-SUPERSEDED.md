# Aborted-Pair Supersession Notice

- **Scope ID:** `6f781a4d-661a-4630-8def-911d80d753e3`
- **CampaignSet Record SHA-256:** `543bbbb5fd28b6d0a6cf3aaa2acbac2df30801b458f0ab5543201d2d26d018af`
- **EvaluationDeclaration SHA-256:** `c06d01bba1cc8b47f154860dfc04367dd43ec14631f036c5f98c0de4417fe842` (Rekor log index 2706919023)
- **DisclosureRequest SHA-256:** `6d04ed3e37c6dc7cfd332243a981834fb78c5d6129107fb1caf93a3aa0358743` (Rekor log index 2706927295)
- **DisclosureReceipt SHA-256:** `8eb964ccf11cf6391f246c82652abff0c799cf9062bd2ec879f62c25a582d2e9` (Rekor log index 2706937560)
- **EvidenceReleaseManifest SHA-256:** `ef4984732945c48c537d82a3e51a1aecc2c2f5ced746c9df05ea1ce5df90bea0` (Rekor log index 2706989586)
- **Dispatched PairIntent SHA-256:** `46a6a9fae416e648c1e64c057aed2c14c78d98d007b869fcd7499d65e64de1c6` (pair index 0, AG-012 `86a807b3-52ca-4fbf-8f5f-8bf4b2b1b935`, anchored)
- **Pre-dispatch Checkpoint SHA-256:** `c5b32bc52e5c25356ccfad4d447ef769e1739805c07728193fa75865b9164a29` (sequence 0, anchored)
- **Post-pair Checkpoint SHA-256:** `1ede75987603f77786d9bf225765a81f7e03312b2e62dbfdc32350dfb62edaba` (sequence 1, terminal `incomplete`, 0 members, 0 model responses, anchored)
- **Supersession Record SHA-256:** `76e4ae1e37907f3a4e6d440243d0a3db45ffac0ba044e2d995a36ebcba4e6032`
- **Signature Envelope SHA-256:** `600b1c00bfa53bf57f3fd3f200e6913745d896b35f6082f563baaf1ec4b01e20`

## Terminal Facts

- **Dispatched PairIntents:** 1 (pair 0 only; never executed)
- **Executed Pairs:** 0
- **Dispatched Members:** 0
- **Model Requests:** 1 — readiness prompt `Reply with exactly: OK` only (`resp_003e3d319a5b45a2016a9a47d0307087d0a792c8f7576a125f`, sealed subscription cost null)
- **Scenario Prompts to Model:** 0
- **Member Transcripts:** 0
- **Provider Egress Opened:** false
- **Pair OAuth Checkout Performed:** false (run failed before `checkout-oauth-profile`)
- **Reason:** Scope superseded after aborted pair 0: the schema-1.6 controller emits journal state `CHECKOUT_OAUTH_PROFILE`, which the trial-journal allowlist did not contain (`unknown trial state`), aborting every pair deterministically at that state. Fixed in source `e1e73cf480927f2c6816d167a202813f1cc75ee2` (allowlist schema-1.6 OAuth checkout/checkin trial states + regression test). The fix changes frozen `adapter_sha256`, so the campaign must be refrozen under a new scope; this scope cannot run further.

Calibration scope `6f781a4d-661a-4630-8def-911d80d753e3` is superseded. Must not be resumed or combined with later scope. Historical releases and the aborted-pair records stay intact and remain verifiable.
