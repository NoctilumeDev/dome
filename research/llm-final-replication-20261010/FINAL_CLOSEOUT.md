# Final frozen replication closeout

## Execution

- State: `FULL_MATRIX_COMPLETE`.
- Physical model calls: 8,220 / 8,220; all transport records are `SUCCESS` and all usage records are present.
- Second-window suites: `time-day1` 72, `query-day1` 234, `query-review-day1` 468.
- All three live 24-hour and Shanghai-date gates passed using actual observed times.
- `SECOND_WINDOW_STATUS.json` records `fullMatrixComplete=true` and `credentialsCleared=true`.
- `SECOND_WINDOW_WAIT_STATUS.json` records `SECOND_WINDOW_COMPLETED`, no credential references held, and credentials cleared.
- No third collection, human repeat, new case family, model, parameter, strategy, product repair, IR implementation, CRUD experiment, or distributed experiment was started.

## Evidence

- Full-matrix provenance receipt: 13/13 suites pass frozen input, fresh identity/order, payload, and reviewer-candidate binding checks.
- Full-matrix resource receipt: 8,220 requests, 7,403,999 reported tokens, zero missing usage.
- Unchanged native replays retain returned sets, session actors, scope-confirmation controls, and read-only snapshots.
- `FINAL_RESULTS.md` records the final cross-day query-control comparison and the qualification ledger.
- `output/final-summary.png` is a derived visual receipt. JSONL, JSON, CSV, logs, seal files, and scorer outputs remain the controlling evidence.

## Writing outputs

The complete paper draft and invention-patent candidate draft are stored only in the private local directory `D:\ResearchEvidence\llm-manuscripts`. They are not committed to this repository or published by this closeout. The old frozen observation manuscripts remain unchanged.

The paper reports only the controlled single-node, read-only, finite-capability definition domain. The patent candidate separates current implementation facts, further candidate embodiments, and untested effects; it does not pre-judge novelty or inventiveness.

## Qualification and remaining work

- Formal human effectiveness remains `PENDING_HUMAN_STUDY`; P01 is retained once as a single-participant exploratory pilot and is not repeated.
- External benchmark transfer remains `CONFOUNDED` where capability/entry semantics conflict with the mapped oracle.
- Error dependence and universal natural reviewer net benefit remain `NOT_IDENTIFIABLE`.
- Actual cash charge and promotional offsets remain `NOT_VERIFIED`; frozen-price estimates are not cash.
- Before submission or patent filing, authorship, affiliation, references, model metadata, ethics/open-data statements, applicant/inventor information, prior-art search, self-disclosure audit, claim scope, and legal review require human confirmation. The private `交付前人工核对清单.md` records these items.

## Hygiene

Research evidence, Git history, seal files, the original first failures, and prior HOLD material are retained. Shared MySQL/Redis were not touched. Temporary test helpers, cache directories, and backend build targets are not evidence and must remain uncommitted; if automated deletion is not authorized, their exact paths are reported for manual cleanup rather than removed through an alternate route.
