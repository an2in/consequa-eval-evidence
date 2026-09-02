# Pre-inference supersession notice

Status: `SUPERSEDED_BEFORE_INFERENCE`

This calibration scope was externally declared and received an exact-scope
disclosure acknowledgment, but it was never released as a precommit bundle and
never reached OAuth, VM execution, scenario dispatch, or model inference.

Deterministic auditor packaging stopped fail-closed when an atomic rename
crossed filesystem boundaries (`EXDEV`). The repair is source commit
`eec3ad566a05b74b51c01ac71e2679f2941ef446`. To avoid silently changing an
externally declared source identity, the operator froze replacement scope
`5a13beda-d11f-43e6-ac7d-2e6635928268` instead of reusing this scope.

The declaration, disclosure request, disclosure receipt, signatures, and
immutable external anchors for this scope remain preserved as evidence of the
aborted pre-inference path. They are not calibration results and must never be
counted as attempts or trial members.
