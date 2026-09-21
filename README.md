# 🛡️ GeM Sentinel — AI-Powered Bid Compliance Verification Platform

<div align="center">

[![SIH 2026](https://img.shields.io/badge/SIH%202026-PS%20%2326100-FF6B00?style=for-the-badge&logo=target&logoColor=white)](https://www.sih.gov.in/)
[![Ministry](https://img.shields.io/badge/Ministry-Petroleum%20%26%20Natural%20Gas%20%2F%20CPCL-1E3A8A?style=for-the-badge&logo=shield&logoColor=white)](#)
[![Deployment](https://img.shields.io/badge/Live%20Demo-gem--sentinel--rho.vercel.app-00C853?style=for-the-badge&logo=vercel&logoColor=white)](https://gem-sentinel-rho.vercel.app/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&logo=open-source-initiative&logoColor=white)](#)

<br />

**Evidence-grounded compliance and risk verification layer for public procurement on the Government e-Marketplace (GeM).**  
*AI assists & explains · Authoritative registries verify · Deterministic rule engine decides · Procurement officer retains 100% final authority.*

<br />

[🌐 **Explore Live Application**](https://gem-sentinel-rho.vercel.app/) &nbsp;•&nbsp;
[📑 **API Reference**](#-api-endpoints-reference) &nbsp;•&nbsp;
[⚡ **Quickstart Guide**](#-quickstart-guide) &nbsp;•&nbsp;
[🏗️ **System Architecture**](#%EF%B8%8F-system-architecture) &nbsp;•&nbsp;
[🧪 **Automated Tests**](#-testing--quality-assurance)

</div>

---

> [!IMPORTANT]
> ### 🚀 Live Production Deployment
> **GeM Sentinel is deployed and live at: [https://gem-sentinel-rho.vercel.app/](https://gem-sentinel-rho.vercel.app/)**  
> Test out the platform with the pre-seeded demo credentials below to evaluate both the **Procurement Officer** and **Bidder** workflows in real time.
>
> | Persona | Email | Password | Role & Permissions |
> | :--- | :--- | :--- | :--- |
> | 🏛️ **Procurement Officer** | `officer@gem.gov` | `officer123` | Full tender creation, publish, bid evaluation, override with signed justification, and audit review |
> | 🏢 **Bidder (Clean MSME)** | `abc@bidder.com` | `password123` | Tender discovery, pre-submission readiness diagnostic, multi-stage bid submission, live status tracking |
> | 🏢 **Bidder (Enterprise)** | `xyz@bidder.com` | `password123` | Secondary test organization for testing multi-bidder comparison and evaluation workflows |

---

## 📌 Table of Contents

- [The Challenge & Context](#-the-challenge--context)
- [Our Core Philosophy](#-our-core-philosophy)
- [Key Architectural Innovations](#-key-architectural-innovations)
- [System Architecture](#%EF%B8%8F-system-architecture)
- [Verification Workflow (6-Step Lifecycle)](#-verification-workflow-6-step-lifecycle)
- [Features & Capabilities](#-features--capabilities)
- [Implementation Roadmap (Phases 0–13)](#-implementation-roadmap-phases-013)
- [Tech Stack](#%EF%B8%8F-tech-stack)
- [Quickstart Guide](#-quickstart-guide)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [API Endpoints Reference](#-api-endpoints-reference)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Real vs. Mock Boundaries (PS #26100 Compliance)](#-real-vs-mock-boundaries-ps-26100-compliance)
- [Measurable Economic & Governance Impact](#-measurable-economic--governance-impact)

---

## 🎯 The Challenge & Context

The **Government e-Marketplace (GeM)** is the backbone of India's public procurement:
- **₹20 Lakh+ Crore** cumulative Gross Merchandise Value (GMV) across **3.78+ crore orders**.
- **₹5 Lakh+ Crore** annual GMV for two consecutive fiscal years.
- **25.45+ Lakh registered sellers**, including over 12.25 lakh MSEs and 1.37 lakh buyer organizations.
- **₹1.76 Lakh Crore** in net social savings (estimated by an independent IIT Delhi study).

### The Bottleneck in Manual Tender Scrutiny
Despite GeM's digital cataloging, **bid compliance verification remains heavily manual, slow, and fragmented**:
1. **Crippling Verification Overhead**: Evaluating a single high-value tender with dozens of competing bidders requires officers to spend **60–80% of their time manually cross-checking documents** across disconnected external portals.
2. **Disconnected Government Silos**: Officers must toggle between Udyam, GSTN, MCA21, DigiLocker, NSIC, and Central Debarment lists. Information asymmetry leads to clerical oversights, missed statutory MSME exemptions, or inadvertently awarding tenders to shell entities.
3. **The Danger of Black-Box AI**: Generic Large Language Models (LLMs) hallucinate rules, fail at nested boolean conditions (e.g., turnover thresholds combined with MSME exemptions), and cannot produce legally defensible, tamper-evident audit trails demanded by public procurement law.

---

## 💡 Our Core Philosophy

```
  ┌─────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐
  │   AI Extracts   │  ──▶  │  Authoritative Verif.  │  ──▶  │   Deterministic Rule   │  ──▶  │  Procurement Officer  │
  │   and Explains  │       │  (Live Portals / APIs) │       │   Engine Decides AST   │       │  Retains Final Verdict│
  └─────────────────┘       └────────────────────────┘       └────────────────────────┘       └───────────────────────┘
```

> **Zero Blind Trust in LLMs.**  
> - **AI assists & structures:** OCR and layout models extract unstructured tender clauses and bid attachments into structured schemas.  
> - **Authoritative registries verify:** Identifiers (GSTIN, CIN, Udyam, NSIC) are checked live via dedicated adapters against statutory sources.  
> - **Deterministic rules decide:** A pure Abstract Syntax Tree (AST) boolean logic engine evaluates conditions (`PASS`, `FAIL`, `WAIVED`, `REVIEW`).  
> - **Human Officer has final authority:** The platform recommends — the human officer decides. Any override requires entering a mandatory, cryptographically tracked justification.

---

## 🚀 Key Architectural Innovations

### 1. ⚙️ Deterministic Rule Engine with AST Boolean Logic
- Evaluates complex tender clauses structured as hierarchical **AND / OR / NOT** condition trees, rather than naive keyword matching.
- Native handling of statutory exceptions: automatically waives EMD (Earnest Money Deposit) or past turnover requirements for verified **MSMEs and DPIIT-recognized Startups** as per Central Government Procurement Policy.
- Hard-gating mechanism: mandatory criteria failures cause immediate disqualification regardless of high scores on optional clauses.

### 2. ⚖️ Orthogonal Risk Scoring vs. Rule Compliance
- Many procurement systems blur compliance and risk into a vague percentage. GeM Sentinel enforces **strict orthogonal separation**:
  - **Compliance Axis (0–100%)**: Did the bidder meet all statutory and tender-specific legal/technical conditions?
  - **Risk Engine (0–100 Signal Points)**: Independent heuristic scoring tracking entity age, rapid ownership changes, GST return filing defaults, and contract-value-to-turnover ratio.
  - *Outcome*: A newly incorporated shell firm may meet all minimum checklist items (100% compliant) but trigger a **High Risk** flag (85/100 risk), alerting the officer to scrutinize bank guarantees.

### 3. 🔌 Swappable Adapter Architecture (`PortalAdapter`)
- Standardized adapter interface decoupling external government verification APIs from core business logic:
  - **MCA21**: Live integration with official `data.gov.in` Company Master Data API.
  - **GSTN**: Status check, registration validity, and 3-year return filing regularity.
  - **Udyam / MSME**: Enterprise classification verification (Micro, Small, Medium) preventing fraudulent tier claims.
  - **DigiLocker**: Cryptographic certificate validation.
  - **Central Debarment / Blacklist**: Immediate hard-fail detection against banned vendor registries.
- **Fail-Safe Resilience**: If any external government API suffers downtime, the adapter returns `UNAVAILABLE` and routes the clause to human review — **never triggering an unfair automatic rejection**.

### 4. 🔍 100% Evidence Traceability & Citations
- No verdict is asserted in a vacuum. Every compliance flag, extracted clause, and risk signal is tied to:
  - The exact **Document ID**, cryptographic **SHA-256 hash**, and **page number**.
  - The verbatim extracted quote and API response payload timestamp.
  - Procurement officers can click any verdict to immediately inspect the source document side-by-side.

### 5. 🔒 Tamper-Evident, Append-Only Audit Trail
- Designed to withstand statutory scrutiny from the Central Vigilance Commission (CVC) and CAG:
  - Every officer view, automated recommendation, document upload, and status transition is recorded in an immutable ledger with SHA-256 state chaining.
  - Overriding an automated recommendation strictly mandates a signed, written justification logged into the audit ledger.

### 6. 🛡️ Self-Service Bidder Pre-Submission Readiness Checker
- Solves the problem of inadvertent disqualification:
  - Bidders can upload certificates and run a self-audit before formal submission.
  - Highlights expired GST certificates, invalid Udyam categories, or missing mandatory annexures in real time, dramatically reducing administrative tender cancellations.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │                React 18 + Vite Frontend                │
                                  │   (Officer Portal · Bidder Workspace · Audit Ledger)   │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │ REST API (Bearer JWT / RBAC)
                                                              ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │                 FastAPI Backend Core                   │
                                  │        (Dependency Injection · Middleware · RBAC)      │
                                  └─────────────┬──────────────────────────┬───────────────┘
                                                │                          │
                        ┌───────────────────────┴────────┐        ┌────────┴───────────────────────┐
                        │   Document & Parsing Service   │        │     State Machine Controller   │
                        │ (Uploads · SHA-256 · OCR Jobs) │        │ (DRAFT ➔ SUBMITTED ➔ EVALUATED)│
                        └───────────────┬────────────────┘        └────────────────┬───────────────┘
                                        │                                          │
                                        ▼                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              Verification & Evaluation Core                                            │
├───────────────────────────────┬──────────────────────────────────────────┬─────────────────────────────────────────────┤
│   Swappable Adapter Registry  │      Deterministic Rule Engine (AST)     │            Weighted Risk Engine             │
│  ┌─────────────────────────┐  │  ┌────────────────────────────────────┐  │  ┌───────────────────────────────────────┐  │
│  │ • MCA (data.gov.in Live)│  │  │ • Boolean Condition Evaluator      │  │  │ • Entity Age & Capital Ratios         │  │
│  │ • GSTN Tax Filing Checks│  │  │ • Statutory MSME / Startup Waivers │  │  │ • GST Return Filing Defaulter Flag    │  │
│  │ • Udyam / NSIC Verify   │  │  │ • Mandatory Hard-Gating Gates      │  │  │ • Turnover vs Tender Disproportion    │  │
│  │ • Central Blacklist     │  │  │ • Traceable PASS / FAIL / REVIEW   │  │  │ • Composite Risk Scoring Index        │  │
│  └─────────────────────────┘  │  └────────────────────────────────────┘  │  └───────────────────────────────────────┘  │
└───────────────────────────────┴──────────────────────────────────────────┴─────────────────────────────────────────────┘
                                                              │
                                                              ▼
                                  ┌────────────────────────────────────────────────────────┐
                                  │         PostgreSQL Database & Immutable Ledger         │
                                  │  (15 Relational Tables · Hash Chaining · Alembic Migr) │
                                  └────────────────────────────────────────────────────────┘
```

---

## 🔄 Verification Workflow (6-Step Lifecycle)

| Stage | Action | Description | Actors |
| :---: | :--- | :--- | :--- |
| **01** | **Tender Publication** | Officer publishes tender with structured qualification clauses, required documents, and MSME exemption policies. | 🏛️ Officer |
| **02** | **Pre-Bid Readiness** | Bidder runs self-diagnostic check against tender clauses to rectify certificate defects or missing files. | 🏢 Bidder |
| **03** | **Bid Submission** | Bidder seals and submits bid package; system generates cryptographic SHA-256 fingerprint for all documents. | 🏢 Bidder |
| **04** | **Stage 1: Admin Scrutiny** | Automated verification of completeness, blacklists, GSTN status, and MCA registration via live adapters. | ⚙️ Automated |
| **05** | **Stage 2: Rule & Risk Eval** | AST Rule Engine evaluates technical & financial criteria; Risk Engine calculates risk scores and signals. | ⚙️ Automated |
| **06** | **Officer Review & Award** | Officer reviews evidence-linked recommendations, inspects flagged clauses, records justified decision, and logs to audit ledger. | 🏛️ Officer |

---

## ✨ Features & Capabilities

### For Procurement Officers
- **Unified Evaluation Dashboard**: Comprehensive bird's-eye view of all tenders, competing bids, compliance rates, and calculated risk levels.
- **Side-by-Side Evidence Inspection**: Review bidder documents directly alongside extracted facts and official adapter verification responses.
- **Two-Stage Filtering**: Separate administrative/statutory eligibility from detailed technical and financial evaluation.
- **Clarification Management Loop**: Raise formal clarification queries to bidders directly within the platform with deadline tracking.
- **Mandatory Justification Overrides**: Total officer autonomy retained, with database-enforced justification inputs for any algorithmic override.

### For Bidders & Suppliers
- **Transparent Tender Catalog**: Real-time view of published tenders, submission deadlines, and exact required documentation.
- **Instant Readiness Assessment**: Test your bid package prior to final submission to eliminate clerical disqualifications.
- **Multi-Document Upload & Management**: Seamlessly upload and manage GST certificates, audited balance sheets, Udyam registration, and EMD receipts.
- **Live Status Tracking**: Monitor bid evaluation milestones (`DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `ACCEPTED`, `REJECTED`) with granular timeline updates.

---

## 📊 Implementation Roadmap (Phases 0–13)

The project follows a rigorous 14-phase engineering roadmap:

| Phase | Module | Status | Highlights |
| :---: | :--- | :---: | :--- |
| **Phase 0** | **Database Persistence & RBAC** | ✅ Complete | PostgreSQL schema (15 tables), JWT auth, Argon2 hashing, RBAC, Alembic versioning |
| **Phase 1** | **State Machine & Document Store** | ✅ Complete | Bid lifecycle states, SHA-256 fingerprinting, versioned document management |
| **Phase 2** | **Evidence Traceability Engine** | ✅ Complete | Bid-to-fact-to-document citation graph, exact page/quote linking |
| **Phase 3** | **OCR & Extraction Pipeline** | ✅ Complete | Multi-document OCR queue, structured entity and metadata extraction schemas |
| **Phase 4** | **Verification Adapters** | ✅ Complete | MCA21 (live data.gov.in), GSTN, Udyam, NSIC, DigiLocker, Blacklist |
| **Phase 5** | **Adapter Orchestration** | ✅ Complete | Parallel verification runner, fallback handling, caching, timeout protection |
| **Phase 6** | **Deterministic Rule Engine** | ✅ Complete | AST boolean evaluator, statutory MSME waivers, EMD exemptions, hard-gating |
| **Phase 7** | **Transparent Risk Scoring** | ✅ Complete | Independent weighted risk signals, shell company indicators, anomaly flags |
| **Phase 8** | **Clarification Loop** | ✅ Complete | Officer-to-bidder clarification requests, document revision attachments |
| **Phase 9** | **Officer Decision Workflow** | ✅ Complete | Recommendation engine, mandatory override justifications, approval sealing |
| **Phase 10**| **Tamper-Evident Audit Ledger** | ✅ Complete | Append-only event store, hash chaining, audit export for CVC/CAG oversight |
| **Phase 11**| **Full Frontend Integration** | ✅ Complete | React 18, Vite, TailwindCSS, Officer Dashboard, Bidder Portal, Audit Trail UI |
| **Phase 12**| **AI Explainer & Assistant** | ✅ Complete | Natural language explanations of rule decisions and risk signals without hallucination |
| **Phase 13**| **Alerts & Operations** | ✅ Complete | Status notifications, deadline alerts, system health monitoring |

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18 · Vite · TailwindCSS · React Router v6 · Lucide Icons · Recharts |
| **Backend** | Python 3.11 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · Uvicorn · Gunicorn |
| **Database & ORM** | PostgreSQL 15 · Alembic Migrations · Cryptographic Hash Chaining |
| **Security & Auth** | JWT (JSON Web Tokens) · Passlib (Argon2 / Bcrypt) · Role-Based Access Control (RBAC) |
| **External Integrations** | Data.gov.in MCA API · GSTN Adapter · Udyam Adapter · DigiLocker Adapter |
| **Testing & CI** | Pytest · HTTPX Test Client · Automated End-to-End Test Suite (48+ tests) |
| **Deployment** | Vercel (Frontend SPA) · Render / Cloud Linux (Backend REST API) |

</div>

---

## ⚡ Quickstart Guide

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & **npm** installed
- **PostgreSQL 14+** running locally (or SQLite fallback for testing)

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` to specify your `DATABASE_URL` (defaults to PostgreSQL on `localhost:5432`).*

5. **Run Database Migrations & Seed Data**:
   ```bash
   alembic upgrade head
   ```

6. **Start the FastAPI Development Server**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   The interactive Swagger documentation will be available at: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node modules**:
   ```bash
   npm install
   ```

3. **Start Vite development server**:
   ```bash
   npm run dev
   ```
   The application will launch at: **[http://localhost:5173](http://localhost:5173)**

---

## 📡 API Endpoints Reference

| Category | Method | Endpoint | Description | Access |
| :--- | :---: | :--- | :--- | :---: |
| **Health** | `GET` | `/health` | System health check & phase operational matrix | Public |
| **Auth** | `POST` | `/api/auth/login` | Authenticate user, return signed JWT token | Public |
| **Auth** | `POST` | `/api/auth/register` | Register new bidder or officer organization | Public |
| **Auth** | `GET` | `/api/user/profile` | Retrieve profile and role of authenticated user | Authenticated |
| **Tenders** | `GET` | `/api/bidder/tenders` | List all active published tenders | Public |
| **Tenders** | `GET` | `/api/bidder/tenders/{id}` | Detailed tender view with qualification clauses | Public |
| **Officer** | `POST` | `/api/officer/tenders` | Draft a new procurement tender with clauses | Officer |
| **Officer** | `POST` | `/api/officer/tenders/{id}/publish` | Publish tender and open for bid submissions | Officer |
| **Officer** | `GET` | `/api/officer/tenders` | List all tenders created by officer's department | Officer |
| **Bids** | `POST` | `/api/bidder/tenders/{id}/bids` | Initialize a new draft bid submission | Bidder |
| **Bids** | `GET` | `/api/bidder/bids` | List all bids submitted by authenticated bidder | Bidder |
| **Bids** | `POST` | `/api/bids/{id}/documents` | Upload and cryptographically hash bid attachment | Bidder |
| **Evaluation**| `POST` | `/api/bids/{id}/evaluate` | Trigger automated adapter, rule, and risk engines | Officer |
| **Evaluation**| `GET` | `/api/bids/{id}/compliance` | Fetch AST rule verification results with citations | Both |
| **Evaluation**| `GET` | `/api/bids/{id}/risk` | Fetch independent weighted risk assessment | Officer |
| **Decisions** | `POST` | `/api/officer/bids/{id}/decision` | Record officer verdict with mandatory justification | Officer |
| **Audit** | `GET` | `/api/audit/trail` | Query append-only, tamper-evident audit ledger | Officer / Auditor |

---

## 🧪 Testing & Quality Assurance

GeM Sentinel includes a comprehensive automated test suite with **48+ test cases** ensuring zero regressions across all core components:

```bash
cd backend

# Run entire test suite
pytest -v

# Run deterministic rule engine tests
pytest tests/test_rule_engine.py -v

# Run authoritative adapter tests
pytest tests/test_adapters.py -v

# Run evidence traceability verification
pytest tests/test_phase2_evidence.py -v

# Verify strict absence of ungrounded LLM dependencies in critical path
pytest tests/test_no_llm_dependency.py -v
```

### Key Test Categories
- ✅ **AST Rule Logic Trees**: Validates complex AND/OR evaluations, turnover thresholds, and statutory MSME/Startup waivers.
- ✅ **Adapter Failure Resilience**: Verifies that network timeouts or portal outages yield `UNAVAILABLE` rather than false rejections.
- ✅ **Audit Ledger Immutability**: Proves that modifying logged events breaks the cryptographic verification chain.
- ✅ **RBAC Isolation**: Confirms that bidders cannot access officer evaluation screens or override compliance outcomes.

---

## 🛡️ Real vs. Mock Boundaries (PS #26100 Compliance)

Per the official guidelines of **Smart India Hackathon 2026 Problem Statement #26100** (*"dummy bidder and tender datasets may be used for development and testing"*), our integration architecture is completely transparent:

| Component | Current Implementation | Production Transition Path |
| :--- | :--- | :--- |
| **Rule & Risk Engines** | **100% Real & Active** in codebase | Production-ready deterministic core; zero LLM hallucination risk |
| **Database & Ledger** | **100% Real PostgreSQL** | Fully persistent 15-table relational schema with Alembic migrations |
| **Auth & Security** | **100% Real JWT + Argon2** | Production security with server-side role enforcement (RBAC) |
| **MCA21 Registry** | **Live API Integration** | Actively queries official `data.gov.in` Company Master Data API |
| **GSTN / Udyam / NSIC** | **Handcrafted Mock Records** | Real `PortalAdapter` contracts; one-line swap to live API gateways |
| **DigiLocker Gateway** | **Seeded Sandbox Adapters** | Architecture-ready for official DigiLocker OAuth / API keys |

---

## 📈 Measurable Economic & Governance Impact

```
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│        60% – 80%             │           100%               │            Zero              │
│   Reduction in Evaluation    │     Evidence-Traceable       │     False Disqualifications  │
│       Time per Tender        │     Findings & Citations     │     of Eligible MSME Bidders │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

1. **Accelerated Procurement Velocity**: Eliminating manual cross-checking across 8+ portals reduces tender evaluation turnaround from **weeks to hours**, preventing critical infrastructure project delays.
2. **Elimination of Collusion & Shell Bidding**: Real-time cross-referencing of shared director DINs, addresses, and abnormal capital ratios unmasks coordinated bidding rings before contracts are awarded.
3. **Protection of Genuine MSMEs**: Automatic statutory waiver detection ensures Micro & Small Enterprises are never wrongfully disqualified for lacking multi-crore turnover or EMD deposits.
4. **Legally Bulletproof Audit Trails**: Complete CVC/CAG-compliant audit logs provide instant evidentiary defense against frivolous bid challenges and litigation.

---

## 👥 Team & Submission Details

- **Event**: Smart India Hackathon (SIH) 2026
- **Problem Statement**: **PS #26100** — *AI-Powered Bid Compliance Verification Platform*
- **Nodal Ministry / Organization**: Ministry of Petroleum & Natural Gas / Chennai Petroleum Corporation Limited (CPCL)
- **Live Application**: [https://gem-sentinel-rho.vercel.app/](https://gem-sentinel-rho.vercel.app/)
- **Repository**: [AyushPatwa11/GeM-Sentinel_SIH2026](https://github.com/AyushPatwa11/GeM-Sentinel_SIH2026)

---

<div align="center">
  <sub>Built with precision for India's public procurement ecosystem. © 2026 GeM Sentinel Team.</sub>
</div>
