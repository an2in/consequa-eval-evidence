# Pre-inference supersession notice

Calibration scope `84aee450-2aef-46ad-bb9d-89083435309c` is superseded.
It must not be resumed or combined with a later calibration scope.

The scope reached an operator-signed and externally anchored immutable
precommit for CalibrationSet
`de7c7e0b528e089bc2c9afc11f31302388ed0dc2be24640d6616f147fe4b7c8a`.
The operator authorized DisclosureRequest
`acb68278117d9f175c0ebd351dfdbccc0f5093d9df8fb15a1523bc009e375a35`
and canonical DisclosureReceipt
`4fd8bf00061eac4a7b7a375369b17b5be2ba0ae875f60c235428dff3c903413e`
was signed and externally anchored.

When calibration execution was initiated with `--pair-limit 1`, the runner
stopped at the preflight state-reconstruction gate before dispatching any
scenario, readiness prompt, or inference request. The guest helper failed closed
because the sealed guest state baseline required helper `f5f13b59ddd8ddd2d4dbe59edf60700cf909579b736477c300bdd471fb7f6341`,
whereas the signed implementation commit `34b0a7186e435082831316e0bdffc206cb9ea99a`
requires helper `b9e111a4f0f773f6f096dcb2b85ecb32ae1784197cfa6f57489d7daa7203a31b`.

At supersession:
- exactly zero PairIntents existed;
- exactly zero calibration pairs were dispatched;
- exactly zero calibration members were dispatched;
- exactly zero model requests occurred;
- no prompt, tool output, or model response was sent;
- the active OAuth lease `32c73e1d-d6de-49e4-92ca-a93f36146930` remained vaulted;
- provider egress remained closed;
- trial services remained inactive;
- all historical immutable release assets remain intact on the public ledger.

Governance remains cryptographic auditability without independent human review.
