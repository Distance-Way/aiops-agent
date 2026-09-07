# 03 — Worker Runtime

**What to build:** A Worker process can register itself, heartbeat, poll for jobs, execute controlled diagnostic/inference job types, and report results back to the Control Plane.

**Blocked by:** 02 — Scheduling and Job Lifecycle

**Status:** ready-for-agent

- [ ] Worker command registers with API and runs a polling loop.
- [ ] Job types system_status, service_check and query_logs execute through existing controlled tool logic.
- [ ] log_inference jobs execute through the local deterministic model.
- [ ] Worker handles execution errors and reports a failed job result.
