# Implementation Plan: Comprehensive Iranian IPG Gateway Adapters Suite

**Branch**: `003-implement-ipg-adapters` | **Date**: 2026-10-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-implement-ipg-adapters/spec.md`

## Summary

Expand the IPG Sandbox engine to provide full, authentic drop-in emulation for all 13 Iranian payment gateways documented in `./docs/` (Behpardakht, ZarinPal, IDPay, Saman SEP, Sadad Melli, Parsian PEC, Pasargad PEP, Asan Pardakht, Pardakht Novin, IranKish, SizPay, Fanava Card, and Bank Sarmayeh). The system supports native wire protocols (SOAP 1.1/1.2 XML WSDL contracts and REST JSON endpoints), authentic token generation, gateway-branded checkout pages, Shaparak-compliant HTTP POST/GET callbacks, realistic cardholder/trace metadata (masked PAN, RRN), permissive cryptographic signature handling (RSA/HMAC), and comprehensive scenario mapping across all 6 universal lifecycle states.

## Technical Context

**Language/Version**: Python 3.12 (engine), TypeScript / Node 20 (dashboard)

**Primary Dependencies**: FastAPI (async web engine), SQLAlchemy 2 + Alembic (PostgreSQL persistence), httpx (async callbacks/webhooks), defusedxml / xml.etree (SOAP XML parsing and generation), cryptography (optional strict RSA/HMAC verification), Next.js 14+ (dashboard)

**Storage**: PostgreSQL 16 (transactions, adapter configurations, delivery attempts, meter stats)

**Testing**: pytest (unit, integration, and contract tests), Playwright (dashboard & checkout flow verification)

**Target Platform**: Linux/macOS/Windows dev environments via Docker Compose or standalone local python process

**Project Type**: web-service (modular backend engine + frontend dashboard)

**Performance Goals**: Endpoint responses < 200ms locally; webhook delivery < 500ms; WSDL service documents returned < 50ms

**Constraints**: Drop-in client compatibility without requiring code modifications in merchant apps; zero external network dependencies on Shaparak or banking production switches; permissive signature validation by default; canonical Rial accounting internally

**Scale/Scope**: 13 adapter implementations, 13 gateway route modules, 6 universal simulation scenarios, realistic mock metadata generators

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` is an unfilled template with no ratified project rules. Constraints applied derive directly from `specs/003-implement-ipg-adapters/spec.md`, `specs/001-mvp/plan.md`, and `specs/002-backend-api-alignment/plan.md`:
- Pure drop-in emulation (no client changes except base URL).
- Canonical Rial internal storage.
- Non-breaking backward compatibility with existing Behpardakht, ZarinPal, and IDPay adapters.
- Gate status: **PASS**.

**Post-Phase-1 re-check**: PASS — Design artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) adhere to the single engine architecture, maintain backward compatibility, and avoid adding unneeded dependencies or breaking existing data models.

## Project Structure

### Documentation (this feature)

```text
specs/003-implement-ipg-adapters/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output: protocol research, gateway analysis, signature strategy
├── data-model.md        # Phase 1 output: provider enums, credential schemes, metadata models
├── quickstart.md        # Phase 1 output: validation scenarios and curl verification commands
├── contracts/           # Phase 1 output: wire-level adapter contracts
│   └── adapter-surfaces.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
apps/engine/
├── src/
│   ├── adapters/
│   │   ├── base.py                   # PaymentAdapter base class + credential verification
│   │   ├── metadata.py               # Deterministic masked PAN, RRN, trace generators
│   │   ├── crypto.py                 # Permissive/strict RSA and HMAC signature helpers
│   │   ├── asan_pardakht/            # Asan Pardakht adapter + routes
│   │   ├── behpardakht/              # Behpardakht Mellat adapter + SOAP routes
│   │   ├── fanava/                   # Fanava Card adapter + routes
│   │   ├── idpay/                    # IDPay REST adapter + routes
│   │   ├── irankish/                 # IranKish adapter + routes
│   │   ├── pardakht_novin/           # Pardakht Novin (PNA) adapter + routes
│   │   ├── parsian/                  # Parsian (PEC) adapter + SOAP routes
│   │   ├── pasargad/                 # Pasargad (PEP) adapter + REST routes
│   │   ├── sadad/                    # Sadad (Bank Melli) adapter + REST/SOAP routes
│   │   ├── saman/                    # Saman (SEP) adapter + routes
│   │   ├── sarmayeh/                 # Bank Sarmayeh adapter + routes
│   │   ├── sizpay/                   # SizPay REST adapter + routes
│   │   └── zarinpal/                 # ZarinPal REST adapter + routes
│   ├── models/
│   │   └── enums.py                  # Expanded Provider enum (13 providers)
│   ├── checkout/
│   │   └── page.py                   # Multi-gateway branded checkout renderer
│   └── api/
│       └── app.py                    # Gateway router registrations
tests/
├── unit/
│   └── test_adapters_metadata.py     # Metadata and signature tests
└── contract/
    └── test_all_adapters_contracts.py# Wire protocol contract tests for all 13 gateways
```
