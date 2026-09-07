# 01 — Worker and Diagnostic Job API

**What to build:** A user or Worker operator can register a Worker with CPU/memory capacity, submit a Diagnostic Job with priority and resource requests, list jobs, and read individual job state. This is an end-to-end API slice even before scheduling runs.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Worker registration endpoint stores id/name/capacity and returns the Worker.
- [x] Job submission endpoint accepts type, priority, resource requests and payload.
- [x] Job list and detail endpoints expose status and timestamps.
- [x] Existing Agent chat tests still pass.

## Answer

Implemented Worker registration/list and Diagnostic Job create/list/detail HTTP endpoints with SQLite persistence and HTTP-level tests.
