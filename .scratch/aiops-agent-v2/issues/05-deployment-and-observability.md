# 05 — Deployment and Observability

**What to build:** The v2 platform can start locally with Docker Compose as a Control Plane plus Worker, deploy with Kubernetes manifests, and expose queue/Worker/job metrics to Prometheus/Grafana.

**Blocked by:** 03 — Worker Runtime

**Status:** ready-for-agent

- [ ] Docker Compose runs api and worker services from the same image.
- [ ] Kubernetes manifests describe Control Plane and Worker deployments with services/config.
- [ ] Prometheus metrics include workers, queued jobs and completed jobs.
- [ ] CI validates tests, compose config and Docker image build.
