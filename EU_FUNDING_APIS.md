# EU Funding APIs — Research Reference

Generated: 2026-03-28. All endpoints verified via live requests.

---

## 1. TED (Tenders Electronic Daily) API v3

### Base Info
- **OpenAPI Spec**: `https://api.ted.europa.eu/api-v3.yaml`
- **Swagger UI**: `https://api.ted.europa.eu/swagger-ui.html`
- **Swagger Config**: `https://api.ted.europa.eu/v3/api-docs/swagger-config`
- **Version**: 3.0.0
- **Docs Portal**: `https://docs.ted.europa.eu`

### Authentication
- Global security scheme: `token: []` (API key)
- **Search endpoint is PUBLIC** — `security: []` (no auth required)
- Submission/conversion endpoints require API key via `Authorization` header
- API keys managed via `/v3/api-keys/{token}/renew`
- Keys obtained by registering at eNotices2

### Search Endpoint (the main one for scraping)
```
POST https://api.ted.europa.eu/v3/notices/search
Content-Type: application/json
```

**Request Schema** (`PublicExpertSearchRequestV1`):
```json
{
  "query": "TD=3",
  "fields": ["BT-01-notice", "publication-date", "deadline-receipt-tender-date-lot"],
  "limit": 100,
  "page": 1
}
```

Required fields:
- `query` (string) — Expert search query syntax (NOT JSON array syntax)
- `fields` (array of strings) — Which fields to return per notice

Optional:
- `limit` (int) — Results per page
- `page` (int) — Page number
- `paginationMode` — PAGE_NUMBER or ITERATION (for large result sets use ITERATION with `iterationNextToken`)

**Response Schema** (`ExpertSearchResponse`):
```json
{
  "notices": [
    {
      "publication-number": "106253-2016",
      "publication-date": "2016-03-30+02:00",
      "links": {
        "xml": {"MUL": "https://ted.europa.eu/en/notice/106253-2016/xml"},
        "pdf": {"ENG": "...", "ELL": "..."},
        "html": {"ENG": "https://ted.europa.eu/en/notice/-/detail/106253-2016"}
      },
      "<requested-field>": "<value>"
    }
  ],
  "totalNoticeCount": 12345,
  "iterationNextToken": "..."
}
```

### Expert Query Syntax
Uses TED's own query language (NOT SQL, NOT Lucene):
- `TD=3` — Contract notices (TD = Type of Document; 3 = Contract notice)
- `TD=7` — Contract award notices
- `PD=20260327` — Publication date (NOT array syntax `PD=[...]`)
- `CY=GR` — Country (Greece)
- `PC=72000000` — CPV code (IT services)
- `AND`, `OR`, `NOT` operators
- Example: `TD=3 AND CY=GR AND PD>=20260301`

### Key Returnable Fields (for `fields` array)
| Field Name | Description |
|---|---|
| `BT-01-notice` | Notice legal basis |
| `publication-date` | Publication date |
| `deadline-receipt-tender-date-lot` | Submission deadline |
| `contract-nature-main-proc` | Contract nature (works/supplies/services) |
| `identifier-part` | Notice identifier |
| `submission-url-lot` | Where to submit |
| `place-of-performance-country-proc` | Country |
| `framework-estimated-value-glo` | Estimated value |
| `framework-maximum-value-lot` | Maximum framework value |
| `organisation-name-buyer` | Buyer name |
| `BT-24-Procedure` | Description/title |
| `BT-21-procedure` | Title |
| `BT-22-procedure` | Internal ID |
| `BT-262-procedure` | Main CPV code |
| `BT-539-Lot` | Award criterion type |
| `AA` | Authority activity |
| `AC` | Award criteria |

Full list: returns in error message when invalid field is sent.

### Other Endpoints
- `POST /v3/notices/submit` — Submit notice (auth required)
- `POST /v3/notices/validate` — Validate notice XML
- `POST /v3/notices/convert` — Convert old XML to eForms
- `POST /v3/notices/render` — Render to PDF/HTML
- `GET /v3/config/sdk-versions` — eForms SDK versions

### Rate Limits
Not documented in the OpenAPI spec. No rate limit headers observed. Recommend conservative polling (1 req/sec max).

### No RSS Feed
The new TED portal does NOT provide RSS feeds. The old `ted.europa.eu/TED/` had RSS but the v3 API replaces it entirely.

---

## 2. EU Funding & Tenders Portal (FTOP / SEDIA)

### SEDIA Search API
```
POST https://api.tech.ec.europa.eu/search-api/prod/rest/search
Content-Type: application/x-www-form-urlencoded
```

**Parameters** (form-encoded, NOT JSON):
```
apiKey=SEDIA
dataSetId=cftDataset
text=*
pageSize=10
pageNumber=1
```

- `apiKey=SEDIA` — Public, no registration needed
- `dataSetId=cftDataset` — Call for Tenders/Proposals dataset
- `text` — Free text query (`*` for all)
- `pageSize` — Results per page (max ~100)
- `pageNumber` — 1-indexed
- `sortBy` — Sort field
- `groupByField=sortStatus` — Group by status

**Response Format**:
```json
{
  "text": "*",
  "totalResults": 634563,
  "pageNumber": 1,
  "pageSize": 10,
  "results": [
    {
      "reference": "...",
      "url": "https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/TOPIC-ID.json",
      "summary": "Topic title text",
      "language": "en",
      "database": "SEDIA",
      "weight": 1.0,
      "groupById": "3",
      "metadata": { ... }
    }
  ]
}
```

### Key Metadata Fields (per result)
| Field | Description |
|---|---|
| `title` | Topic title |
| `identifier` | Topic identifier (e.g., HORIZON-CL4-2025-DATA-01-01) |
| `callIdentifier` | Parent call ID |
| `callTitle` | Parent call title |
| `status` | Open/Closed/Forthcoming |
| `sortStatus` | Status sort code (1=Forthcoming, 2=Open, 3=Closed) |
| `deadlineDate` | Submission deadline |
| `startDate` | Opening date |
| `budgetOverview` | Budget information |
| `frameworkProgramme` | Programme ID |
| `programmePeriod` | Programme period |
| `programmeDivision` | Programme division/cluster |
| `typesOfAction` | RIA, IA, CSA, etc. |
| `keywords` | Topic keywords |
| `tags` | Tags |
| `focusArea` | Focus area |
| `crossCuttingPriorities` | Cross-cutting priorities |
| `descriptionByte` | Full HTML description |
| `actions` | JSON array of action details (deadlines, types) |
| `deadlineModel` | Deadline model info |
| `topicConditions` | Eligibility conditions |

### Topic Detail JSON (Direct)
Each topic has a direct JSON URL:
```
GET https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/{TOPIC_ID}.json
```
Example: `https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/HORIZON-CL5-2025-D3-01-01.json`

### Filtering Open Calls
To get only open/forthcoming calls:
```
apiKey=SEDIA&dataSetId=cftDataset&text=*&pageSize=50&pageNumber=1&groupByField=sortStatus
```
Then filter by `groupById`: `"1"` = Forthcoming, `"2"` = Open, `"3"` = Closed.

Or use metadata filter (if supported by dataset) to restrict to `status` values.

### RSS / Atom Feeds
**No official RSS feed.** The portal is a Single Page App (Angular). Must use the SEDIA API.

### Rate Limits
Not documented. The `apiKey=SEDIA` is a public key. Recommend max 1 request/second.

---

## 3. CORDIS (Community Research and Information Service)

### Search API
```
GET https://cordis.europa.eu/search/en?q={query}&format=json&num={count}&p={page}
```

**Parameters**:
- `q` — Query string (e.g., `*`, `contenttype='project'`, `programme/code='HORIZON'`)
- `format=json` — Response format
- `num` — Results per page
- `p` — Page number (1-indexed)

**Response Format**:
```json
{
  "result": {
    "header": {
      "numHits": "1",
      "totalHits": "1160197",
      "records": "1-1",
      "sortBy": "Relevance:decreasing"
    }
  },
  "hits": {
    "hit": {
      "project": {
        "language": "en",
        "rcn": "284864",
        "id": "101231504",
        "acronym": "CHRONOPOP",
        "teaser": "Project description...",
        "objective": "Full objective text..."
      }
    }
  }
}
```

### Key Project Fields
- `rcn` — Record Control Number (unique)
- `id` — Project grant ID
- `acronym` — Project acronym
- `teaser` — Short description
- `objective` — Full objective
- `programme/code` — Programme (HORIZON, H2020, etc.)

### Authentication
None required. Public API.

### Limitations
- CORDIS is for **funded projects**, NOT open calls
- Useful for tracking which proposals got funded
- Search API can return HTML (302 redirect) if Accept header isn't set

---

## 4. Other Relevant Sources

### data.europa.eu
- EU Open Data Portal: `https://data.europa.eu/api/hub/search/datasets?q=TED&limit=10`
- Contains TED bulk data downloads (XML archives)
- SPARQL endpoint for structured queries

### SIMAP (Supplier Information)
- `https://simap.ted.europa.eu`
- CPV code reference data
- Buyer profiles

### EDF / Horizon Europe / DIGITAL
All use the same FTOP/SEDIA portal — filter by `frameworkProgramme`:
- Horizon Europe: programmePeriod = `2021-2027`, programme = `HORIZON`
- Digital Europe: programme = `DIGITAL`
- EDF (European Defence Fund): programme = `EDF`
- LIFE: programme = `LIFE`
- CEF (Connecting Europe Facility): programme = `CEF`
- Erasmus+: programme = `ERASMUS`

---

## Python Client Architecture (Recommended)

```python
"""Minimal polling structure for daily scraper."""

# 1. TED — New contract notices published today
import requests
from datetime import date

def poll_ted_new_notices(pub_date: str = None):
    """Search TED for notices published on a given date."""
    if not pub_date:
        pub_date = date.today().strftime("%Y%m%d")
    resp = requests.post(
        "https://api.ted.europa.eu/v3/notices/search",
        json={
            "query": f"TD=3 AND PD={pub_date}",
            "fields": [
                "BT-01-notice",
                "publication-date",
                "deadline-receipt-tender-date-lot",
                "contract-nature-main-proc",
                "place-of-performance-country-proc",
                "submission-url-lot",
                "framework-estimated-value-glo",
            ],
            "limit": 100,
            "page": 1,
        },
    )
    resp.raise_for_status()
    return resp.json()


# 2. FTOP — Open calls for proposals
def poll_ftop_open_calls(page: int = 1, page_size: int = 50):
    """Search SEDIA for open/forthcoming funding calls."""
    resp = requests.post(
        "https://api.tech.ec.europa.eu/search-api/prod/rest/search",
        data={
            "apiKey": "SEDIA",
            "dataSetId": "cftDataset",
            "text": "*",
            "pageSize": page_size,
            "pageNumber": page,
            "groupByField": "sortStatus",
        },
    )
    resp.raise_for_status()
    data = resp.json()
    # Filter to open (2) and forthcoming (1) only
    return [
        r for r in data.get("results", [])
        if r.get("groupById") in ("1", "2")
    ]


# 3. FTOP — Get full topic details
def get_topic_details(topic_id: str):
    """Fetch full JSON for a specific topic."""
    resp = requests.get(
        f"https://ec.europa.eu/info/funding-tenders/opportunities/data/topicDetails/{topic_id}.json"
    )
    resp.raise_for_status()
    return resp.json()


# 4. CORDIS — Recently funded projects
def search_cordis_projects(query: str = "*", num: int = 10, page: int = 1):
    """Search CORDIS for funded projects."""
    resp = requests.get(
        "https://cordis.europa.eu/search/en",
        params={"q": query, "format": "json", "num": num, "p": page},
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()
```

---

## Key Gotchas

1. **TED query syntax**: NOT Lucene — uses `FIELD=VALUE` with `AND/OR/NOT`. No brackets `[]` for date values.
2. **TED fields required**: The search endpoint REQUIRES the `fields` array — it won't return data without it.
3. **SEDIA is form-encoded**: Must use `Content-Type: application/x-www-form-urlencoded`, NOT JSON.
4. **No RSS anywhere**: Neither TED v3 nor FTOP provide RSS/Atom feeds. Must poll APIs.
5. **CORDIS is post-hoc**: Shows funded projects, not open calls.
6. **Topic detail URLs are predictable**: `topicDetails/{TOPIC_ID}.json` — can fetch details directly if you know the ID.
7. **Pagination**: TED supports both page numbers and iteration tokens. For large sweeps, use ITERATION mode.
