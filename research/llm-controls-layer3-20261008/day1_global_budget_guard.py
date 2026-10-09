"""Add the later query package to the global budget without changing frozen calls."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import collect

R = Path(__file__).resolve().parent
QUERY = R.parent / "llm-query-controls-20261008"
original_check = collect.check


def global_check():
    original_check()
    first = collect.read(R / "results/day0/summary.json")
    finish = datetime.fromisoformat(first["finishedAt"])
    now = datetime.now(timezone.utc)
    assert (now - finish).total_seconds() >= 86400
    shanghai = timezone(timedelta(hours=8))
    assert now.astimezone(shanghai).date() > finish.astimezone(shanghai).date()
    baseline = collect.read(QUERY / "output-v2/physical-resources.json")["providers"]
    current = collect.lines(R / "results/day1/calls.jsonl")
    reserve = collect.read(R / "plan.json")["unknownReserveCny"]
    for provider in ("deepseek", "qwen"):
        added = sum(
            c["estimatedCostCny"] if c["estimatedCostCny"] is not None else reserve
            for c in current if c["provider"] == provider
        )
        if baseline[provider]["conservativeCumulativeCny"] + added + 0.10 > 20:
            raise RuntimeError("GLOBAL_BUDGET_BOUNDARY")


if __name__ == "__main__":
    import sys
    assert not (R / "results/day1").exists(), "Existing day1 is not implicitly resumed"
    global_check()
    collect.check = global_check
    sys.argv = [str(R / "collect.py"), "day1", "--keys-stdin"]
    collect.main()
