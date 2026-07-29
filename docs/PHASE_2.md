# Phase 2 — Streaming pipeline

**Goal:** turn the offline prototype into a live system that scores transactions as they
arrive. This is where the project stops being a notebook and becomes engineering.

---

## Step 1 — Emit events to a stream

Add a **stream mode** to the generator: instead of writing a CSV, it publishes transaction
events onto **Redis Streams**, one at a time, at a configurable rate. Keep the event shape
identical to the Phase 1 schema (`src/common/schema.py`).

## Step 2 — Build the streaming feature engine

This is the core challenge. In batch you had the whole history in a DataFrame; now events
arrive one at a time and you must **hold state**:

- keep a per-card sliding window of recent transactions (timestamps, amounts, locations),
- on each new event, update the window and compute the same velocity features as Phase 1,
- evict old entries as they age out.

The streaming features **must match** the batch features for the same input — this is the
training/serving consistency problem. Write a test that feeds the same sequence through both
paths and asserts the features agree.

## Step 3 — Build the scoring consumer

A service that consumes the stream, calls the feature engine, runs the model, and emits a
decision (fraud probability + flag). Write each decision to the store alongside the
transaction.

## Step 4 — Measure latency

Instrument the end-to-end path (event received → decision emitted). Record p50 and p99.
This number is a headline result of the project — knowing it, and being able to talk about
what drives it, is exactly what a fintech interviewer wants.

---

## Deliverable

A running pipeline: generator → Redis Streams → scoring consumer → store, scoring live
transactions, with latency measured.

## Common pitfalls

- **Unbounded state** — evict old window entries or memory grows forever.
- **Training/serving skew** — if streaming and batch features disagree, the model sees
  inputs it was never trained on. Test for parity.
- **Blocking the consumer** — keep the per-event work lean to protect latency.
