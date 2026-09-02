# Pre-inference supersession notice

Status: `SUPERSEDED_BEFORE_INFERENCE`

This replacement calibration scope was externally declared and received an
exact-scope disclosure acknowledgment, but it was never released as a
precommit bundle and never reached OAuth, VM execution, scenario dispatch, or
model inference.

After the deterministic archive staging repair, packaging stopped fail-closed
at the equivalent atomic-install boundary for the OpenPGP ciphertext. The
encryption helper still staged its output under `/tmp`, so `os.replace` raised
`EXDEV` when the evidence directory was a different filesystem. Source commit
`9f36de63c994972ade24e4ab281e9b63f23f4572` repairs both atomic staging
boundaries and adds regression coverage for each.

To avoid changing an externally declared source identity, the operator froze
replacement scope `ccc49b55-9b28-4baa-9573-8c29855d82bd`. A complete local
packaging rehearsal for the replacement source passed before its public key
registration. This scope's declaration, disclosure records, signatures, and
anchors remain preserved, but they are not calibration results and must never
be counted as attempts or trial members.
