# Pre-inference supersession notice

Calibration scope `b2503cd4-d57b-4e0a-bf85-d8bf906cdd45` is superseded.
It must not be resumed or combined with a later calibration scope.

The scope reached an operator-signed and externally anchored immutable
precommit for CalibrationSet
`bef22c60336d9ad3b1dc58529373eb2f8d7b236f43d4a61ee19d58bf8e1f19e8`.

At supersession:
- exactly zero calibration pairs were dispatched under this scope;
- exactly zero model requests occurred under it;
- no PairIntent, readiness prompt, or scenario inference was dispatched;
- no provider response ID or transcript exists;
- this scope was superseded solely because the implementation source commit changed from `802a11bb2ffbf7c5d309dcc92d560f1a4a5b7fce` to `34b0a7186e435082831316e0bdffc206cb9ea99a` following independent audit verification and fail-closed OAuth durability hardening;
- historical evidence remains available and immutable in public releases and ledger records.

Governance remains cryptographic auditability without independent human review.
