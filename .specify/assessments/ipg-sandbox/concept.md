# Concept: Free Self-Hostable Payment-Gateway Sandbox

- **Slug**: ipg-sandbox
- **Created**: 2026-09-23
- **Recommended option**: Option B — AGPL Open-Core Sandbox Platform (trimmed v1)

## Options

### Option A — Mock Library Only (smallest thing that could work)

- **Sketch**: Ship an AGPL open-source package (Python, with JS helpers later) that developers install into their app to stub gateway calls in-process: scenario fixtures for approve/decline/timeout against Zarinpal/IDPay-style APIs, runnable in CI with zero infrastructure. No dashboard, no hosted service — the "product" is the library and its fixture files.
- **Appetite**: small (days)
- **Trade-offs**: Wins: fastest zero-cost entry, no hosting/metering/auth to build, trivially free forever. Sacrifices: misses three of five stated goals (professional bilingual dashboard, hosted demo launch, one consistent multi-provider surface); no drop-in remote-API story (banktest's core DX); weak competitive narrative — libraries don't demo well in Persian dev channels. Risk: library-only OSS is easily ignored next to a panel product.
- **Rabbit holes**: creeping toward "let's add a tiny UI anyway" (which becomes Option B piecemeal); fixture fidelity debates per gateway.

### Option B — AGPL Open-Core Sandbox Platform (trimmed v1) — recommended

- **Sketch**: A self-hostable sandbox product: run one Docker Compose on localhost and your app talks to emulated gateway endpoints (swap URL/credentials, no core code changes — banktest DX parity) with a professional Linear-dark bilingual dashboard showing transactions and forcing scenarios (approve/decline/timeout/refund per stage), plus webhook/callback delivery to your app. v1 = 2–3 adapters (Zarinpal, IDPay, Behpardakht WSDL), free forever via AGPL self-hosting; a free hosted demo goes live the same day as the public repo. Cloud tiers/teams/billing exist only as deferred structure, not built in v1.
- **Appetite**: medium (weeks — sized as a hard ~1-month MVP budget)
- **Trade-offs**: Wins: meets all five goals (free/self-host, scenario coverage, consistent surface, professional bilingual UX, 1-month launch); directly counters banktest.ir's paywall + hosted-only model; adapter interface leaves room for Stripe later. Sacrifices: a month of the requester's personal time; two-service system (engine + dashboard) means auth, i18n/RTL, and Postgres to maintain; WSDL fidelity likely won't be byte-perfect against real Behpardakht on day one. Risks: unmeasured demand (problem.md open question); Behpardakht SOAP emulation is the schedule's biggest unknown.
- **Rabbit holes**: (1) WSDL drop-in fidelity — chasing banktest-perfect SOAP behavior can eat the whole budget; (2) adapter count inflation — the 11-gateway wish-list slipping back into v1; (3) record & replay / live proxy scope creep (a prioritized UVP, but post-v1); (4) cloud tunnel agent for hosted webhooks; (5) multi-tenant hosted auth + metering polish; (6) RTL/bilingual QA breadth.

### Option C — No Product: Free DIY Fixtures on Top of Existing Mocks (buy/don't-build)

- **Sketch**: Instead of building a simulator, publish free scenario-fixture templates + tutorials (e.g. for WireMock/MSW) covering common Iranian gateway flows, and point users to banktest.ir (or live bank test ports) for full emulation. The "release" is a repo of fixtures and blog posts.
- **Appetite**: small (days)
- **Trade-offs**: Wins: near-zero build and maintenance cost; still free for users; validates demand cheaply via community response. Sacrifices: no dashboard, no hosted demo, no unified multi-provider surface, no drop-in DX — fails goals 3–5 outright; hands the free/self-host axis back to nobody (banktest stays unchallenged); no real asset to monetize later. Risk: confirms demand but leaves the problem standing if fixtures get no traction.
- **Rabbit holes**: tutorials expanding into a quasi-product; zero ownership of UX means the "professional UI" ask goes unanswered.

## Recommendation

**Option B.** It is the only option that clears the problem's bar: zero-cost self-hosted entry (vs banktest's verified no-free-tier), full scenario coverage, one consistent surface, a professional bilingual dashboard, and a public repo + hosted demo inside the ~1-month appetite — Option A and C both fail three-plus goals and would not support the adoption/UX success metrics. It also preserves the deferred cloud-tier structure without building billing now (problem non-goal). Option C's cheap demand test can run *alongside* B (fixtures repo published first), not instead of it.

## Out of Scope (for the recommended option)

- Real payment processing/settlement, production traffic, compliance/KYC/licensing (inherited non-goals).
- Commercial billing system and payments entity (deferred until revenue); exact Pro-tier pricing.
- More than 2–3 adapters in v1 (full wish-list and bank ports = post-v1); Stripe/PayPal = phase 2.
- Byte-perfect gateway emulation on day one.
- Record & replay live proxy, cloud tunnel agent for webhooks, AI-assisted tests, packaged CLI/SDK (prioritized UVPs, explicitly post-v1).
- Team workspaces / cloud scenario library / paid-tier features (structure reserved; built when cloud monetization starts).

## Assumptions to Validate

- Demand exists for a free/self-hostable alternative — appetite in the Persian dev community is unmeasured (problem.md open question); validate via fixtures-repo-first or waitlist/star signal at launch.
- The requester can sustain aggressive ~1-month effort on a personal project (nights/weekends constraint unknown — feasibility check for decide).
- Behpardakht WSDL emulation can reach "swap URL + credentials" drop-in quality within the budget (schedule's top technical risk — spike early in specify).
- AGPL-3.0 is acceptable to the target audience and sufficient to protect the cloud tier.
- Hosted demo on personal infra with no billing stays low-cost and low-liability (simulation only, no real money, no card data).
- banktest.ir's verified facts (pricing, gateways, capabilities, 2026-09-23) remain current at launch.
