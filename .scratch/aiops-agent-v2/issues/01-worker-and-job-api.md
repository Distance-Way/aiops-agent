# 01 — Worker and Diagnostic Job API

**What to build:** A user or Worker operator can register a Worker with CPU/memory capacity, submit a Diagnostic Job with priority and resource requests, list jobs, and read individual job state. This is an end-to-end API slice even before scheduling runs.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Worker registration endpoint stores id/name/capacity and returns the Worker.
- [ ] Job submission endpoint accepts type, priority, resource requests and payload.
- [ ] Job list and detail endpoints expose status and timestamps.
- [ ] Existing Agent chat tests still pass.
