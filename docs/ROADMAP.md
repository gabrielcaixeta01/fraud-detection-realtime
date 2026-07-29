# Roadmap

The project is built in four phases. Each phase ends with something **functional** — you
should never be stuck in a limbo with nothing to show. The estimated pace assumes you are
building alongside other commitments; adjust freely.

The guiding principle throughout: **the model is the easy part. The system around it is the
point.** Spend your effort on the streaming, the live features, the latency, and the drift
monitoring — that is what makes this project rare.

---

## Phase 1 — Data generator + offline baseline (weeks 1–2)

**Goal:** produce realistic synthetic transactions and prove a model can separate fraud
from non-fraud offline.

- Build the transaction generator: model *normal* user behavior (home location, typical
  amounts, usual hours) and inject realistic *fraud* patterns (bursts, impossible geographic
  velocity, amounts far above the user's baseline, card-testing micro-transactions).
- Label the data — you know the ground truth because you generated it.
- Engineer velocity features **in batch first** (in a DataFrame — easier to debug than
  streaming).
- Train a baseline: start with **LightGBM/XGBoost**, not deep learning.
- Evaluate with the **right** metrics for imbalance: precision/recall and PR-AUC — never
  raw accuracy.

**Deliverable:** a notebook that proves the model separates fraud from non-fraud, plus a
reusable data generator.

See [`PHASE_1.md`](PHASE_1.md) for implementation detail.

---

## Phase 2 — Streaming pipeline (weeks 3–4)

**Goal:** turn the offline prototype into a live system.

- Have the generator emit events into a stream (start with **Redis Streams** — simpler than
  Kafka; migrate later if you want the name on your CV).
- Build the scoring service that consumes the stream.
- Recompute velocity features **in real time** — now you must hold state (sliding windows
  per card). This is the engineering core of the project.
- Call the model and emit a decision.
- Measure end-to-end latency.

**Deliverable:** a running system that scores transactions live.

See [`PHASE_2.md`](PHASE_2.md).

---

## Phase 3 — Production + drift monitoring (weeks 5–6)

**Goal:** make it look and behave like production.

- Package in Docker; expose scoring as a **FastAPI** endpoint.
- Add a monitoring dashboard (Streamlit, or Grafana to stand out) showing throughput,
  p50/p99 latency, and fraud rate over time.
- **Simulate drift:** change the fraud pattern in the generator partway through, and show
  your monitoring detecting the model's degradation. This demonstration is what makes a
  senior engineer stop and pay attention.

**Deliverable:** a containerized system with a live monitoring dashboard that visibly
catches drift.

See [`PHASE_3.md`](PHASE_3.md).

---

## Phase 4 — Polish + narrative (weeks 7–8)

**Goal:** turn a working system into a portfolio piece that opens doors.

- Write a README that tells the **engineering story**, not just "I used ML to detect
  fraud": architecture decisions, why streaming, how you avoided look-ahead bias in the
  velocity features, latency vs. accuracy trade-offs.
- Add tests (pytest).
- Add an architecture diagram.
- Record a short GIF/video of the system running.

**Deliverable:** a repo that reads as a real engineering project.

See [`PHASE_4.md`](PHASE_4.md).

---

## Where not to slip

The classic mistake that kills fraud projects: spending 90% of the time *tuning the model*
(one more feature, one more round of tuning) and 10% on the system. **Invert that.** Your
differentiator is not the model's F1 score — it is the system around it. A "good enough"
model in an excellent system is worth far more in your portfolio than a perfect model in a
notebook.
