# Pre-inference supersession notice

Calibration scope `713c80fc-8a7e-402d-a822-3357e9653090` is superseded.
It must not be resumed or combined with a later calibration scope.

The scope reached an operator-signed and externally anchored immutable
precommit for CampaignSet
`1a51b041bdf67e76ef834b269bd3d68a6bc8a9e51cbcf76ebacaf3815c43d54c`.
An OAuth lease was then installed, but the first runner command stopped at the
scenario-free readiness checkout gate. The controller's generic JSON client
added a `schema_version` field to an OAuth transaction whose root-owned helper
contract accepts exactly `profile` and `lease_id`. The helper rejected that
request before moving the credential vault into an active profile.

At supersession:

- no `PairIntent` existed;
- no readiness prompt was sent;
- no scenario prompt, fixture tool output, or model response was sent;
- no provider response ID or transcript existed;
- no attempt entered the model phase;
- the only runner artifact was a sanitized pre-inference quota observation;
- the OAuth lease was destroyed and the VM was reconstructed clean, with
  provider egress closed and the VM powered off.

The controller-only contract repair is commit
`802a11bb2ffbf7c5d309dcc92d560f1a4a5b7fce`. The guest helper and sealed
baseline bytes are unchanged. Evaluation continues, subject to a new
declaration, disclosure, encrypted precommit, and OAuth login, under scope
`b2503cd4-d57b-4e0a-bf85-d8bf906cdd45`. This notice records a replacement; it
does not mutate or retract the earlier immutable releases.

Governance remains cryptographic auditability without independent human
review.
