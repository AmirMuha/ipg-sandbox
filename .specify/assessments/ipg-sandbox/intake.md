# Idea Intake: Payment Gateway Simulator (Sandbox)

- **Slug**: ipg-sandbox
- **Created**: 2026-09-23
- **Updated**: 2026-09-23 (clarifications rounds 5–6 applied — all unknowns resolved)
- **Source**: pasted text
- **Type**: new-capability

## Idea (as captured)

> investigate on the following idea, I need your intake on it, the idea is around a payment gateway simulator (sandbox), like sandbox, initial goal is to compete with banktest.ir for iranian developers, and then internaltional ipgs like stripe and other forms of payments globally being used and are common, I need unique value propositions or innovations, unique and UI and dashboards, to look more professional

## Restated

A free, self-hostable payment-gateway sandbox emulating Iranian bank gateways and PSPs (then international IPGs like Stripe) so developers test payment flows without live credentials — winning on professional UX, richer scenarios, and an AGPL open-core with a monetized cloud tier.

## Clarified Scope (requester, 2026-09-23)

- **v1 capabilities**: gateway API emulation; hosted checkout/redirect pages; webhook/callback simulation; transaction lifecycle (approve, decline, timeout, refund, pending→settle); dashboard with test controls. *(CLI/SDK deferred — CI via emulated API + test kit.)*
- **Primary user (v1)**: Iranian developers & startups.
- **v1 gateway shortlist (trimmed)**: Zarinpal + Behpardakht (Mellat PSP) + IDPay. Remaining (NextPay, Saman PSP, Sadad PSP, bank ports Saderat/Melli/Tejarat/Saman) → post-v1, behind the adapter interface. International (Stripe, PayPal) = phase 2.
- **"Compete with banktest.ir" =**: better UX/dashboard, free/open-source, self-hostable, more test scenarios.
- **Delivery model**: OSS self-hostable core (AGPL-3.0) + free hosted instance; cloud SaaS freemium for monetization.
- **License**: AGPL-3.0 for the OSS core.
- **Timeline**: aggressive ~1 month to MVP (public release).
- **Tech stack**: monorepo — Python (gateway engine) + Next.js (dashboard), PostgreSQL, Docker Compose.
- **"v1 launched" =**: public GitHub repo + free hosted demo online.
- **Distribution**: Persian dev communities (primary) + GitHub / HN / Reddit (secondary).
- **Free-tier vs paid split**: OSS/self-host = unlimited forever. Cloud free = 1 project, 1 seat, 7-day history, plus a monthly free request quota. Paid cloud = higher request quotas + longer retention + the gated features below.
- **Paid price point**: teams tier ≈ **99k Toman/mo** (slightly under banktest's 100k Toman/30d); Pro tier adds retention + quota (number TBD at launch).
- **Cloud-only (paid) features**: team workspaces; cloud scenario library; replay/history retention; analytics retention; priority support. *(Core simulation stays free in OSS.)*
- **Webhooks to localhost**: webhook studio ships self-host-first (Docker reaches the host); cloud gets it later via a tunnel agent.
- **Prioritized UVPs**: scenario builder, record & replay, CI-first test kit, multi-provider adapter, webhook studio. *(AI-assisted tests deprioritized.)*
- **Compliance/billing**: defer international billing entity until revenue.
- **UI direction**: dark fintech dashboard, Linear/Vercel-style; bilingual FA/EN (RTL).
- **Origin**: personal side project.
- **Trigger**: personal testing pain — friction hit firsthand.

## Competitor Snapshot: banktest.ir (fetched 2026-09-23)

- **URLs**: https://banktest.ir , https://banktest.ir/pricing/ , https://banktest.ir/faq/ — host: `banktest.ir` — Trust Policy branch: `confirmed-by-user`
- **Model**: hosted-only paid SaaS (panel: `sandbox.banktest.ir`). **No free tier seen.** Time-credit pricing (Toman): 3d = 30,000 · 10d = 50,000 · 30d = 100,000 · 365d = 1,000,000.
- **Capabilities (FAQ/homepage)**: drop-in API simulation — swap WSDL URL + credentials, no core code changes; localhost testing without static IP/Inamad; per-stage response selection; forced timeout/exception; unit-test APIs; no card data collected; generic bank-like UI.
- **Gateways operational (FAQ)**: Saman, Parsian, Mellat, Melli/Sadad, Sepah/Shepard, Pasargad, Asan Pardakht, **Zarinpal (زرین پل — confirmed same as Zarinpal by requester)**, RayanPay; more "in development".
- **Not seen**: open source / self-hosting, webhook studio, record/replay, analytics, team features, international IPGs (Stripe), bilingual RTL/EN focus.
- **Confirmed gap**: IDPay & NextPay not on banktest's operational list.

## Origin & Context

- **Raised by**: the requester — personal side project.
- **Trigger**: personal testing pain — friction hit firsthand.

## Remaining First-Glance Unknowns

- None — intake is fully clarified. Pro-tier price point is a launch-time decision, not a blocker.
