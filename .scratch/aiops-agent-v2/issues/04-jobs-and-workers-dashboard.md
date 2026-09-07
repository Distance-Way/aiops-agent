# 04 — Jobs and Workers Dashboard

**What to build:** The Vue tool page can submit and inspect Diagnostic Jobs and show registered Workers with their capacity and last heartbeat, without breaking the existing conversation page.

**Blocked by:** 02 — Scheduling and Job Lifecycle

**Status:** resolved

- [x] Jobs view lists status and can submit a new job.
- [x] Workers view shows name, capacity and heartbeat state.
- [x] Existing conversation and knowledge base views still work.

## Answer

Added a Vue task scheduling view with Diagnostic Job submission/list and Worker status cards; existing UI tabs remain covered by serving tests.
