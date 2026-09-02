# Pre-inference supersession notice

Status: `SUPERSEDED_BEFORE_INFERENCE`

This calibration scope was externally declared, received an exact-scope
disclosure acknowledgment, and published an immutable encrypted precommit
release. It never created a `PairIntent`, ran the scenario-free readiness
probe, dispatched a scenario or fixture, or performed model inference.

Two OAuth setup flows occurred after the clean no-model gate. The first was
cancelled before authorization because no controller browser session was
available. The second reached the OAuth callback but stopped fail-closed while
the official OpenClaw process attempted to access its disposable auth store.
The store was below the root-owned mode-`0700` runtime directory even though
OpenClaw ran as the unprivileged `foren` account, causing `EACCES`. The helper's
`finally` path removed the disposable login tree and closed provider egress;
post-failure root-helper health reported no OAuth vault and no active copy.
No authorization code, token, account identity, or auth-store bytes are
retained in the public ledger.

Source commit `0deb49f7fef5eb6e7b4b6d31adacd5f55b4827bc` moves the
disposable login tree directly below root-owned `/run`, keeps the leaf mode
`0700`, and adds end-to-end regression coverage for vaulting and cleanup.
Because the helper hash is part of the sealed baseline and frozen source
identity, the operator resealed the baseline and froze replacement scope
`713c80fc-8a7e-402d-a822-3357e9653090` rather than altering this scope.

This scope's declaration, disclosure evidence, encrypted precommit release,
signatures, and transparency-log anchors remain preserved. They are not trial
results and must never be counted as attempts or calibration members.
