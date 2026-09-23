# Decision: Free Self-Hostable Payment-Gateway Sandbox

- **Slug**: ipg-sandbox
- **Decided**: 2026-09-23
- **Verdict**: go
- **Artifacts reviewed**: intake.md | research.md absent | problem.md | concept.md

## Scorecard

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Problem validity | strong | Verified firsthand pain (requester) plus verified structural gaps: banktest.ir has no free tier, is hosted-only, and live-gateway testing needs real money/static IP/Inamad (problem.md, intake snapshot 2026-09-23). |
| Evidence strength | adequate | Competitor side is first-hand verified (banktest.ir home/pricing/FAQ fetched: pricing, gateways, capabilities recorded). Demand side is unmeasured — no research.md; appetite for a free/self-host alternative rests on the requester's observation. One-sided but concrete, not speculative. |
| Value vs. inaction | strong | Free/self-host axis is uncontested today; cost of inaction = continued paywall, live-test risk, rotting DIY mocks, and the launch window lapsing (problem.md). |
| Feasibility / appetite | adequate | Concept Option B fits a hard ~1-month medium appetite with a trimmed 2–3 adapter scope; main schedule risk (Behpardakht WSDL fidelity) is named with an early-spike mitigation; personal-time sustainability assumed, not confirmed. |
| Strategic fit | adequate | No external project constitution exists; aligns with all stated requester goals (AGPL, Python+Next.js monorepo, public repo + hosted demo, Persian-first distribution). Personal side-project concentration risk acknowledged. |
| Risk posture | adequate | Key risks identified with credible mitigations: WSDL spike, adapter-count cap, fixtures-first demand test, billing deferred. Residual unmitigated: unmeasured demand and aggressive timeline on personal bandwidth. |

## Verdict & Rationale

**Go.** Problem validity and value are strong, evidence on the competitive gap is first-hand verified (clearing the evidence bar at `adequate` — never `weak`/`unknown`), and concept.md ships a recommended option (Option B) sized to the stated appetite with named rabbit holes. The honest caveats — unmeasured demand, WSDL schedule risk, personal-time sustainability — are carried forward as open questions rather than blockers; they are exactly the kind of thing specification and early launch signals should resolve, not further assessment stages. Re-running research would mostly re-fetch what intake already verified.

## If go — Handoff to `/speckit.specify`

- **Problem**: Iranian developers can't test payment flows freely/safely — the only local option (banktest.ir) is paid-only and hosted-only; no free, self-hostable, CI-friendly simulator exists (problem.md).
- **Chosen approach**: Concept Option B — AGPL open-core sandbox platform, trimmed v1: Docker Compose self-host (Python engine + Next.js dashboard + Postgres), 2–3 adapters (Zarinpal, IDPay, Behpardakht WSDL drop-in), scenario controls + webhooks + bilingual Linear-dark dashboard; public repo + free hosted demo at launch.
- **In scope / out of scope**: IN — localhost drop-in emulation, transaction lifecycle scenarios, webhook/callback delivery, dashboard with forced-scenario controls, FA/EN RTL, metering structure (no billing). OUT — real payments, billing system/payments entity, >3 adapters, Stripe (phase 2), byte-perfect emulation, record/replay live proxy, cloud tunnel agent, paid-tier features, CLI/SDK, AI tests (concept.md).
- **Success metrics**: zero-cost local entry (banktest baseline: no free tier); time-to-first simulated payment (baseline unknown — measure at demo); scenario coverage per adapter (baseline 0); adoption post-launch (baseline 0); qualitative credibility in Persian dev channels (problem.md).
- **Carried-forward open questions**:
  - Demand validation — appetite unmeasured; mitigate via fixtures-repo-first or launch star/waitlist signal.
  - Behpardakht WSDL drop-in fidelity within budget — spike first during specify.
  - Requester can sustain the aggressive ~1-month personal-project timeline.
  - Pro-tier price point — launch-time decision, not a spec blocker.
  - banktest.ir facts current as of 2026-09-23 — re-verify before public positioning.
