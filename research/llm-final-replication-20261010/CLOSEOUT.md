# First-window closeout

Execution: COMPLETE_FIRST_WINDOW_ONLY. All ten suites completed without transport/usage stop; pipeline PTY11149 exited 0 and cleared its credentials. WINDOW_STATUS.json explicitly leaves fullMatrixComplete=false. No collector or JVM remains from this window. No old request identity was resubmitted.

Evidence: original frozen inputs/runtime unchanged; provenance receipt and resource receipt PASS. Original native/scoring outputs and the derived native reconciliation remain retained. Counterexample analysis ran unchanged against the new identity view. Its first import invocation failed because stats was not on sys.path; the failure is recorded in diagnostics/counterexample-analysis-invocation-first-failure.json. Adding only the original module directory to the invocation repaired it without editing code or making any API call. Old narrative/cumulative price bases in legacy scorer outputs remain legacy; the new resource receipt controls this window's physical accounting.

Next: WAIT_FOR_NEW_24H_WINDOW. Earliest all-guard time: 2026-10-11T03:33:55.087610+08:00. Scheduled automation wake: 2026-10-11T03:35:00+08:00. This replaces the ten-minute patrol. The next stage uses the already sealed second_window.py, then closes the full 8,220-call matrix; no third run. Fresh user-provided keys are required at that window because the prior process keys are cleared.

Local hygiene: owned backend target/helper files are deliberately retained until the final native replays finish. They are temporary, not evidence and not committed. Old HOLD folders and shared MySQL/Redis remain untouched. No deletion was attempted in this closeout. P01 raw data remain in their private archive and the pilot is not repeated. New patent/IR hypotheses remain local.

Research qualification: monetary estimates are not cash payments; tokens are not compute equivalence; repetition is not independent users; strict plan mismatch is not automatically fact error; simulations are not human behavior. This first-window receipt does not finalize paper conclusions or patent validity.
