# EU Funding Monitor — App Concept for Remaco
**Client**: Georg Dafnos, Remaco
**Source**: WhatsApp voice memo, 28 March 2026
**LOSC ref**: `thought:2026-03-28-unnamed`

---

## Problem Statement

Remaco's team currently discovers EU and Greek funding opportunities manually — a time-consuming process that leads to missed calls and wasted effort evaluating calls they can't win. They need an automated, intelligent pipeline that brings relevant opportunities to them daily, pre-filtered against their company profile.

---

## Core Features

### 1. Daily Call Aggregator
Automated daily scraping/API polling of funding sources:

**EU Direct Financing**
- European Commission (TED — Tenders Electronic Daily)
- EU Agencies (EEA, Frontex, EFSA, Europol, etc.)
- Funding & Tenders Portal (FTOP) — the main EU grants portal
- EDIDP / EDF (European Defence Fund — new defence instrument)

**Greek Co-Financed Instruments**
- ΕΣΠΑ 2021-2027 (anaptyxi.gov.gr, logon ΕΣΠΑ)
- Ταμείο Ανάκαμψης και Ανθεκτικότητας (Greece 2.0)
- Ταμείο Δίκαιης Μετάβασης (Just Transition Fund)
- Πράσινο Ταμείο (Green Fund — prasinotameio.gr)
- Ταμείο Μετανάστευσης και Ασύλου (AMIF)
- Ελληνική Αναπτυξιακή Τράπεζα (HDB programmes)

**Delivery**: Daily digest email + in-app dashboard with new/closing-soon calls.

### 2. Company Profile Engine
A structured profile capturing Remaco's capabilities:

| Parameter | Description | Example |
|-----------|-------------|---------|
| **Completed Projects** | Portfolio of past projects with sector, value, client | "ICT modernisation for Municipality X, €450K" |
| **Annual Turnover** | Last 3 years revenue | €2M, €2.3M, €2.5M |
| **Staff** | Headcount by qualification/role | 15 FTE, 3 PhD, 5 MSc |
| **Technical Capacity** | Certifications, ISO, equipment | ISO 9001, ISO 27001 |
| **Sector Experience** | Domains with proven track record | Digital transformation, environment, migration |
| **Geographic Reach** | Countries/regions of operation | Greece, Cyprus, Balkans |
| **Consortium History** | Past partners for joint bids | Partner X (IT), Partner Y (construction) |

### 3. Eligibility Matching Engine
For each incoming call, auto-assess against profile:

- **Turnover thresholds** — does Remaco meet minimum financial capacity?
- **Staff requirements** — key expert CVs available?
- **Sector alignment** — does the call match Remaco's domain expertise?
- **Past project relevance** — similar contracts completed?
- **Geographic eligibility** — is Greece/Remaco's region eligible?

**Output per call**:
- **Match score**: 0-100%
- **Traffic light**: 🟢 Go solo / 🟡 Need consortium partner / 🔴 Not eligible
- **Gap analysis**: "You need ISO 14001" or "Turnover short by €200K — consider consortium"

### 4. Sector Filters & Alerts
- Configurable watchlists by sector/keyword
- Alert thresholds (e.g., only show calls >€100K, match score >60%)
- Deadline proximity warnings (7 days, 3 days, 1 day)

### 5. Consortium Intelligence (Phase 2)
- Suggest potential partners from a maintained partner database
- Flag calls where Remaco could be subcontractor vs lead
- Track partner availability and past collaboration success

---

## Technical Architecture (Proposed)

```
┌─────────────────────────────────────────────┐
│              FRONTEND (Web App)              │
│  Dashboard · Call Browser · Profile Editor   │
│  Filter Config · Email Preferences           │
└──────────────────┬──────────────────────────┘
                   │ REST/GraphQL
┌──────────────────┴──────────────────────────┐
│              BACKEND API                     │
│  Auth · Profile CRUD · Match Engine          │
│  Notification Service · Report Generator     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│           DATA PIPELINE (Daily Cron)         │
│                                              │
│  Scrapers:                                   │
│  ├─ TED API (eu tenders)                     │
│  ├─ FTOP API (eu grants)                     │
│  ├─ anaptyxi.gov.gr (ΕΣΠΑ)                  │
│  ├─ greece20.gov.gr (Recovery Fund)          │
│  ├─ prasinotameio.gr (Green Fund)            │
│  └─ Custom scrapers per source               │
│                                              │
│  NLP Layer:                                  │
│  ├─ Call parsing & field extraction           │
│  ├─ Eligibility criteria extraction           │
│  └─ Sector classification (ML)               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│              DATABASE                        │
│  Calls · Profiles · Match Results · Logs     │
└─────────────────────────────────────────────┘
```

---

## Data Sources — Access Methods

| Source | Method | Notes |
|--------|--------|-------|
| TED (EU tenders) | REST API (free) | ted.europa.eu/api |
| Funding & Tenders Portal | REST API (free) | ec.europa.eu/info/funding-tenders |
| anaptyxi.gov.gr | Web scraping | No public API — needs scraper |
| Greece 2.0 | Web scraping | greece20.gov.gr |
| Πράσινο Ταμείο | Web scraping | prasinotameio.gr |
| AMIF (Migration Fund) | FTOP subset | Filter by programme |
| Defence (EDF/EDIDP) | FTOP subset | Filter by programme |
| Just Transition Fund | FTOP + national | Dual source |

---

## MVP Scope (Phase 1)

1. **TED + FTOP integration** (APIs available — fastest to implement)
2. **Basic company profile** (manual input form)
3. **Keyword/sector matching** (rule-based, no ML yet)
4. **Daily email digest** with matched calls
5. **Simple web dashboard** to browse and filter

**Timeline estimate**: 4-6 weeks for MVP
**Stack suggestion**: Python (FastAPI) + React + PostgreSQL + Celery for daily jobs

---

## Phase 2 Enhancements

- Greek source scrapers (ΕΣΠΑ, Green Fund, Recovery Fund)
- NLP-powered eligibility extraction from call PDFs
- ML sector classification
- Consortium partner database + matching
- Historical analytics (win rate, sector trends)
- Mobile app / push notifications

---

## Open Questions for Georg

1. How many sectors does Remaco actively bid in?
2. What's the typical call value range they target? (€50K–€5M?)
3. Do they need multi-user access (different team members)?
4. Preferred language for the interface — Greek, English, or bilingual?
5. Do they already have a structured project portfolio, or does it need to be built from scratch?
6. Budget range for development?
7. Any existing tools they use for tender monitoring (to integrate or replace)?

---

## MVP Status (Delivered 28 March 2026)

**Live at**: https://ntemiss-mbp.tailddb317.ts.net:8443
**Repo**: github.com/ntemian/remaco-funding-monitor (private)
**Stack**: FastAPI + SQLite + React + Vite

### What's Working
- [x] TED v3 API client (EU tenders — verified field names)
- [x] FTOP/SEDIA API client (EU grants — form-encoded)
- [x] 5-dimension eligibility matching engine (sector/financial/staff/experience/geographic)
- [x] Daily APScheduler pipeline at 07:00
- [x] React dashboard with match stats, donut chart, bar chart
- [x] Funding Calls browser with search/filter + links to original calls
- [x] Eligibility page with score breakdowns and gap analysis
- [x] Company Profile editor with completed projects
- [x] Feedback system (DB-backed, form → API)
- [x] Remaco branding (logo, navy sidebar, blue accent)
- [x] Single-port deployment (FastAPI serves React static)
- [x] Hosted via Tailscale Funnel (HTTPS)

### Known Limitations
- TED/FTOP data is historical (APIs may lag behind live portal)
- Greek sources not yet connected (no public APIs — need scrapers)
- No email digest yet
- Company profile is seeded demo data — Georg needs to fill in real values
- Tailscale Funnel requires Mac to stay awake

---

## Next Steps — Improvement Roadmap

### Phase 2A: Core Value (Immediate)

**1. Daily Email Digest** — Georg's explicit requirement
- Morning email at 07:30 with new/closing calls matched to profile
- HTML template with traffic-light verdicts and one-click links
- Use SMTP or Gmail API

**2. Greek Source Scrapers** — where Remaco actually bids
- `anaptyxi.gov.gr` (ΕΣΠΑ 2021-2027) — Playwright scraper
- `greece20.gov.gr` (Recovery Fund / Greece 2.0)
- `prasinotameio.gr` (Green Fund)
- `diavgeia.gov.gr` (public procurement transparency)
- Schedule: daily at 06:00, before matching pipeline

**3. Real Company Profile** — ask Georg to provide:
- Actual turnover (last 3 years)
- Staff breakdown (total, PhDs, MScs, key experts)
- Completed projects portfolio with values and sectors
- Current certifications (ISO, etc.)
- Active sectors they bid in

**4. AI Call Analysis** — use Claude API to:
- Extract eligibility criteria from call PDFs automatically
- Parse budget breakdowns, lot structures, deadlines
- Classify calls into Remaco's sector taxonomy
- Estimate win probability based on past awards

### Phase 2B: Competitive Advantage

**5. Consortium Intelligence**
- Partner database: who Remaco has worked with, their strengths
- Auto-suggest partners when Remaco lacks capacity
- Track partner availability and past collaboration success

**6. Deadline Management**
- Countdown timers with push notifications (7d, 3d, 1d)
- Expression of Interest tracking
- Go/No-Go decision workflow with team sign-off

**7. Historical Analytics**
- Win rate by sector/source/partner
- Sector trend analysis (which sectors have increasing funding)
- Budget seasonality (when calls typically open)
- Competitor tracking (who wins in Remaco's sectors)

### Phase 3: Scale

**8. Multi-User Access**
- Team login with roles (admin, bid manager, viewer)
- Assignment workflow (who prepares which bid)
- Commenting on calls

**9. Proper Hosting**
- Deploy to VPS or Start9 for 24/7 availability
- PostgreSQL instead of SQLite
- Redis + Celery for background jobs
- Nginx reverse proxy with custom domain (e.g. funding.remaco.gr)

**10. Mobile & Notifications**
- Responsive design / PWA
- Push notifications for new GO matches
- WhatsApp/Telegram alert integration

---

*Saved from WhatsApp voice transcription — Georg Dafnos to Ntemis, 28 March 2026*
