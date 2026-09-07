# 05 — Deployment and Observability

**What to build:** The v2 platform can start locally with Docker Compose as a Control Plane plus Worker, deploy with Kubernetes manifests, and expose queue/Worker/job metrics to Prometheus/Grafana.

**Blocked by:** 03 — Worker Runtime

**Status:** resolved

- [x] Docker Compose runs api and worker services from the same image.
- [x] Kubernetes manifests describe Control Plane and Worker deployments with services/config.
- [x] Prometheus metrics include workers, queued jobs and completed jobs.
- [x] CI validates tests, compose config and Docker image build.

## Answer

Added dual-service Docker Compose, Grafana provisioning, Kubernetes namespace/config/api/worker manifests plus Kind config, Prometheus compute metrics and CI build checks.
