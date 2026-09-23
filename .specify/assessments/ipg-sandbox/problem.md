# Problem Definition: Free, Self-Hostable Testing for Payment Integrations

- **Slug**: ipg-sandbox
- **Created**: 2026-09-23
- **Updated**: 2026-09-23 (refreshed against fully-clarified intake; overwrite confirmed)
- **Inputs used**: intake.md | research.md absent (competitor facts verified inside intake's banktest.ir snapshot)

## Problem Statement

Iranian developers integrating payment gateways cannot safely, quickly, and freely test payment flows before production: testing against live gateways requires real transactions, static IPs, and certifications they don't have, while the one established local alternative (banktest.ir) is a paid-only, hosted-only service (30k–1M Toman time credits, no free tier, no self-hosting). Teams that want — or need — a free, own-infra, CI-friendly way to simulate approve/decline/timeout scenarios have no option today, and the friction of testing international gateways is the same.

## Affected Users & Stakeholders

- **Users**: Iranian developers & startups (primary) — must either pay banktest.ir time credits, test against live bank endpoints with real money/certification risk, or hand-roll fragile mocks; none of these are free or self-hostable.
- **Users**: QA/DevOps engineers on payment-touching products — lack a consistent, automatable way to simulate success/failure/edge-case scenarios in pipelines against local infrastructure.
- **Users**: Developers integrating international IPGs (phase 2) — each provider's sandbox has its own quirks; bespoke mocks per provider are costly (per intake; secondary to v1).
- **Stakeholders**: the requester — personal side project; decides scope, timeline (~1 month MVP), and launch; bears all build/maintenance cost.
- **Stakeholders**: Iranian developer community — affected as the demand signal and adopter base; distribution primary channel (per intake).

## Goals

- Let a developer simulate full payment-flow scenarios (approve, decline, timeout, edge cases) on localhost without live credentials, real money, static IP, or certification.
- Provide a free path forever: unlimited self-hosting (OSS) with an optional free hosted tier — removing banktest.ir's paywall as a barrier to testing.
- Deliver one consistent testing surface covering Iranian bank gateways and PSPs first, extensible to international IPGs later.
- Offer a professional, trustworthy bilingual (FA/EN, RTL) experience so developers choose it over banktest.ir or DIY mocks.
- Reach public v1 (repo + hosted demo) within ~1 month.

## Non-Goals

- Processing or settling real payments — simulation/testing only.
- Replacing production payment providers in live traffic.
- Acting as a compliance, KYC, licensing, or payments-entity product (billing entity deferred until revenue).
- Byte-perfect emulation of every gateway on day one — v1 covers a trimmed shortlist; breadth grows post-launch.
- Building a full commercial billing system in v1 (pricing: launch-time decision).

## Success Metrics

- Time for a new user to simulate a successful payment flow end-to-end (baseline: unknown — depends on banktest signup + credit purchase or live-gateway setup; [NEEDS CLARIFICATION: measure once demo exists]).
- Zero-cost entry: a developer can run the full simulator locally with no payment (baseline: banktest.ir has **no free tier** — verified 2026-09-23; every use requires buying time credits).
- Scenario coverage: approve, decline, timeout/exception, refund, pending→settle exercisable per adapter (baseline: 0 adapters built).
- Adoption: public repo stars + hosted-demo users + projects running it in CI after launch (baseline: 0).
- Qualitative: Persian dev communities rate the dashboard/professional feel as credible vs banktest.ir (qualitative — baseline unknown).

## Cost of Inaction

Nothing is built: Iranian developers keep paying banktest.ir for time-limited hosted access or testing against live gateways with real-money risk and certification friction; no free or self-hostable option ever appears; teams continue maintaining bespoke mocks that rot. The requester's personal-pain fix and the ~1-month launch window lapse, and banktest.ir keeps widening its gateway list unchallenged on the free/self-host axis.

## Open Questions

- [NEEDS CLARIFICATION: Pro-tier price point — launch-time decision, not a problem blocker.]
- [NEEDS CLARIFICATION: demand validation — no formal research stage ran (research.md absent); banktest.ir facts are verified, but appetite for a free/self-host alternative in the target community is unmeasured.]
