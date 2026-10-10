# Credential preload before the unchanged second-window run

The user supplied current credentials on 2026-10-11 before going to sleep and
authorized running the remaining frozen window without waiting for another
reply. `wait_second_window.py` is a timing/input orchestration adapter only.
It takes the credentials through a non-echo PTY now, retains them only in this
one process, and invokes the unchanged `second_window.main()` no earlier than
Shanghai 2026-10-11 03:35. No model API preflight, request, or retry occurs during
the wait. Both the launcher and the original runner validate all three fresh
24-hour/date guards before collection. The collector still rechecks the
applicable guard and original cumulative budget before each request.

The launcher does not alter payloads, identities, order, model settings,
transport, native replay, scorer, first-window results, or the original seals.
Its separate seal pins the launcher, original adapter, source summaries,
eligibility, matrix, and original seal bytes. Its event/status receipts contain
only state, times, PID, guard information and credential lifecycle booleans.
They never contain credential values, hashes, prefixes, environment settings or
process arguments. Credentials are not recovered from any file or transcript.

An existing preload receipt or day1 result prohibits implicit restart. At the
scheduled wakeup, adopt the existing recorded process/session: do not launch a
second collector or ask for credentials while this one is alive. A dead or
failed process is a retained stop requiring reconciliation, not permission to
restart or recover its credentials. Credentials are released when the process
ends. A shutdown loses them; no persistence workaround is authorized.

This adapter has no semantic or product effect. Its preflight is a local
zero-model-call check, and is not another experimental group. The two manuscripts
are written only after the complete matrix and independent receipts are closed.
The paper reports restricted read-only execution, residual semantic errors and
control/reviewer costs; C/U/D were excluded, not empirically demonstrated to be
repaired by fallback. Untested effects stay untested. The patent candidate
follows the user's Word structure and remains private.
