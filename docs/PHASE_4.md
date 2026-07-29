# Phase 4 — Polish + narrative

**Goal:** turn a working system into a portfolio piece that opens doors. Most candidates
stop at "it works." The polish here is what makes the repo memorable.

---

## Step 1 — Write the engineering-story README

The README should read like an engineer explaining decisions, not a tutorial. Cover:
- the architecture and why streaming,
- how you computed velocity features live and kept them consistent with batch,
- how you avoided look-ahead bias,
- the latency vs. accuracy trade-offs you made,
- the drift demonstration and what it shows.

## Step 2 — Add tests

With **pytest**, cover the parts that matter:
- feature correctness (batch vs. streaming parity),
- schema validation,
- a latency-budget check.

A few sharp tests signal engineering maturity that most portfolio projects lack.

## Step 3 — Add visuals

- An architecture diagram (embed it in the README).
- A short GIF or video of the system running and the dashboard catching drift. This is the
  single most effective thing for a reviewer skimming quickly.

## Step 4 — Final pass

- Clean commit history and clear commit messages.
- A `requirements.txt` / lockfile that actually reproduces the environment.
- Make sure `docker-compose up` works from a clean clone.

---

## Deliverable

A repo that reads as a real engineering project: clear story, tested, reproducible, with a
visual that proves it runs.

## The bar to aim for

A reviewer should be able to understand what you built, why, and that it actually runs —
within two minutes of opening the repo, without running anything.
