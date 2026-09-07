# 02 — Scheduling and Job Lifecycle

**What to build:** A registered Worker can claim the highest-priority Diagnostic Job that fits its remaining capacity, complete it with a result or error, and free capacity afterward. Jobs that fit no Worker stay queued.

**Blocked by:** 01 — Worker and Diagnostic Job API

**Status:** ready-for-agent

- [ ] Claim returns the next fitting job ordered by priority then creation time.
- [ ] Claimed jobs transition to running and reserve capacity.
- [ ] Completion succeeds or fails the job and releases capacity.
- [ ] No Worker claim does not fail queued jobs.
- [ ] Heartbeat marks Workers stale so they are not selected.
