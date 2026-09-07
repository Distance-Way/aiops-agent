# 02 — Scheduling and Job Lifecycle

**What to build:** A registered Worker can claim the highest-priority Diagnostic Job that fits its remaining capacity, complete it with a result or error, and free capacity afterward. Jobs that fit no Worker stay queued.

**Blocked by:** 01 — Worker and Diagnostic Job API

**Status:** resolved

- [x] Claim returns the next fitting job ordered by priority then creation time.
- [x] Claimed jobs transition to running and reserve capacity.
- [x] Completion succeeds or fails the job and releases capacity.
- [x] No Worker claim does not fail queued jobs.
- [x] Heartbeat marks Workers stale so they are not selected.

## Answer

Implemented HTTP heartbeat, claim and complete endpoints backed by a capacity-aware scheduler; queue ordering, resource reservation/release and stale-worker behavior are covered by API tests.
