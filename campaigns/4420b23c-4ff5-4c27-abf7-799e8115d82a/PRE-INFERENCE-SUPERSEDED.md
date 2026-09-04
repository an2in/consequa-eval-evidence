# Pre-Inference Supersession Notice

- **Scope ID:** `4420b23c-4ff5-4c27-abf7-799e8115d82a`
- **CampaignSet Record SHA-256:** `3fa699018284578e673aa2916ae16c26e9a28813667f4ff09e669aa3b168c2ed`
- **EvaluationDeclaration SHA-256:** `148fe2c8debc262a9d968b0c85446c74a4eb7b4e2f642854ea7dff862cdf6f74` (Rekor log index 2706442682)
- **DisclosureRequest SHA-256:** `7802bf97b6b892d6caaf4b0bd11066cb1b2fa04618c0eaf5be7d5e1bfc346e33` (Rekor log index 2706454771)
- **DisclosureReceipt SHA-256:** `7d366cc7582b8f2f1158d1836e35c9cf26449ee579616441066ba9e01959587a` (Rekor log index 2706482708)
- **EvidenceReleaseManifest SHA-256:** `72053e268936efc572b784fac350978a86f3890cf266523f241c88e3c2efd7d7` (Rekor log index 2706528980)
- **Supersession Record SHA-256:** `aa7fa71584ba6badcbbedee0a37726fa7ba93670d8c6ebfda7df4574bc8886a2`
- **Signature Envelope SHA-256:** `b291563509216860d538a75fe9bfde4bbdcbe740af87cda3ee667dff1ce9cccd`

## Terminal Facts

- **Dispatched PairIntents:** 0
- **Executed Pairs:** 0
- **Dispatched Members:** 0
- **Model / Readiness Requests:** 0
- **Reason:** Scope superseded prior to inference due to readiness cost-accounting fix (source `e4269dc272572689c1ae56266013cfe794d48ad3` accepts Codex calculated `cost_usd_decimal`) changing frozen `adapter_sha256` (`f78471ac760a…` → `907ed0b1…`); campaign must be refrozen with the fixed source. Runner stopped at preflight hash check before any PairIntent.

Calibration scope `4420b23c-4ff5-4c27-abf7-799e8115d82a` is superseded. Must not be resumed or combined with later scope. Historical releases intact.
