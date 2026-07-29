# Phase 3 — Production + drift monitoring

**Goal:** make the system look and behave like production, and prove it can detect its own
degradation.

---

## Step 1 — Containerize

Write a `Dockerfile` per service and a `docker-compose.yml` that brings up the whole system
(generator, Redis, scoring service, dashboard) with one command. Reproducibility is part of
the deliverable.

## Step 2 — Expose scoring as an API

Wrap the scoring path in a **FastAPI** endpoint (`POST /score`) that accepts a transaction
and returns a decision. This makes the model callable by anything, and demonstrates the
serving skill fintechs hire for.

## Step 3 — Build the monitoring dashboard

Using **Streamlit** (or Grafana), show in real time:
- throughput (transactions/sec),
- latency p50 / p99,
- fraud rate over time,
- feature/prediction distributions vs. the training baseline.

## Step 4 — Demonstrate drift

This is the standout moment of the project. Partway through a run, **change the fraud
pattern** in the generator (e.g. shift the amount anomaly, introduce a new pattern). Then
show your monitoring:
- the live feature/prediction distribution diverging from the training baseline,
- a drift signal firing,
- the model's effectiveness visibly dropping.

Being able to *show* this — not just claim it — is what makes a senior engineer take the
project seriously.

---

## Deliverable

A containerized system, a scoring API, and a live dashboard that visibly catches injected
drift.

## Common pitfalls

- **No baseline to compare against** — capture the training-time distribution so you have
  something to detect drift *from*.
- **Drift demo that is not visible** — make the before/after obvious in the dashboard.
