# Mini Hiring Pipeline

A web application that helps a recruiter manage candidates through a single hiring pipeline and find candidates using a natural-language search box.

Candidates progress through:

```
Applied → Screening → Interview → Offer → Hired
```

A candidate may be rejected from any stage before being hired. Every stage change is recorded as an append-only audit event.

---

## Features

### Pipeline management

- Add candidates.
- View candidates grouped by current stage.
- Advance candidates one stage at a time.
- Reject candidates before they are hired.
- Prevent stage skipping and backward movement.
- Treat Hired and Rejected as terminal stages.
- View complete candidate stage history.
- View how long a candidate has been in the current stage.

### Candidate search

The application provides one natural-language search box supporting:

- Typo-tolerant candidate-name search.
- Current-stage filtering.
- Time-in-stage filtering.
- Historical stage-transition filtering.
- Stage exclusions.
- Combined supported conditions.
- Ranked results.
- Human-readable query interpretation.
- Understandable errors for invalid queries.

**Example searches:**

| Query | Intent |
|---|---|
| `Find Priya Sharam` | Typo-tolerant name search |
| `Who's in Interview right now?` | Current-stage filter |
| `Who has been stuck in Screening for more than a week?` | Time-in-stage filter |
| `Who moved to Interview since Monday?` | Historical stage-transition filter |
| `Who reached the Offer stage but didn't get hired?` | History with exclusion |
| `Everyone except rejected candidates` | Stage exclusion |

---

## Technology stack

### Backend

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | SQLite |
| Fuzzy matching | RapidFuzz |
| Testing | pytest |
| Package manager | uv |

### Frontend

| Component | Technology |
|---|---|
| Library | React 19 |
| Language | TypeScript |
| Build tool | Vite |
| Styling | CSS |
| HTTP | Browser Fetch API |

---

## Project structure

```
hiring_pipeline/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── candidates.py
│   │   │   ├── pipeline.py
│   │   │   └── search.py
│   │   ├── search/
│   │   │   └── parser.py
│   │   ├── services/
│   │   │   ├── candidates.py
│   │   │   ├── search.py
│   │   │   └── transitions.py
│   │   ├── database.py
│   │   ├── errors.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── scripts/
│   │   └── seed_demo_data.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_candidate_details.py
│   │   ├── test_create_candidate.py
│   │   ├── test_health.py
│   │   ├── test_models.py
│   │   ├── test_pipeline.py
│   │   ├── test_search_api.py
│   │   ├── test_search_parser.py
│   │   └── test_transitions.py
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── pipeline.ts
│   │   ├── components/
│   │   │   ├── AddCandidateForm.tsx
│   │   │   ├── CandidateDetailsPanel.tsx
│   │   │   ├── PipelineBoard.tsx
│   │   │   ├── SearchPanel.tsx
│   │   │   └── StageColumn.tsx
│   │   ├── types/
│   │   │   └── pipeline.ts
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── .env.example
│   ├── package.json
│   └── package-lock.json
└── README.md
```

---

## Prerequisites

Install the following:

- **Python 3.12**
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **Node.js** (Vite-compatible version)
- **npm**
- **Git**

---

## Running the backend

From the repository root:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The backend will be available at:

| Endpoint | URL |
|---|---|
| API root | http://127.0.0.1:8000 |
| Interactive docs | http://127.0.0.1:8000/docs |
| Health check | http://127.0.0.1:8000/health |

### Loading demonstration data

The repository includes deterministic, backdated demonstration data covering the required search cases.

From `backend/`:

```bash
uv run python -m scripts.seed_demo_data
```

The seed script resets local candidate and stage-event data before creating:

| Candidate | State |
|---|---|
| Priya Sharma | Currently in Interview |
| Arun Nair | In Screening for more than a week |
| Meera Joseph | Rejected after reaching Offer |
| David Thomas | Currently Hired |
| Neha Kapoor | Currently Applied |
| Ravi Menon | Rejected before reaching Offer |

> **Warning:** The seed command is intended only for local development and demonstration. It deletes existing candidate and stage-event records before recreating the demo dataset.

---

## Running the frontend

Create the local environment file and start the dev server:

**PowerShell:**

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

**Bash / macOS / Linux:**

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend will normally be available at: http://localhost:5173

The expected environment value is:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> Run the backend and frontend in **separate terminals**.

---

## Running tests

### Backend tests

From `backend/`:

```bash
uv run pytest -v
```

The backend test suite covers:

- Candidate creation.
- Initial Applied audit event.
- Valid and invalid stage transitions.
- Stage-skipping prevention.
- Terminal stages.
- Stale transition requests.
- Candidate details and history.
- Current-stage duration.
- Search-plan parsing.
- Search filtering and ranking.
- Valid zero-result searches.
- Invalid-query errors.

### Frontend checks

From `frontend/`:

```bash
npm run lint
npm run build
```

---

## Stage-transition rules

The valid transitions are:

```
APPLIED   → SCREENING or REJECTED
SCREENING → INTERVIEW or REJECTED
INTERVIEW → OFFER or REJECTED
OFFER     → HIRED or REJECTED
HIRED     → (terminal)
REJECTED  → (terminal)
```

The backend is the authoritative source of transition rules. The frontend displays only valid actions, but every transition is validated again by the backend.

Transition requests include both the expected starting stage and target stage:

```json
{
  "from_stage": "SCREENING",
  "to_stage": "INTERVIEW"
}
```

The update is performed conditionally against the stored current stage. A stale repeated request returns **409 Conflict** rather than advancing the candidate twice.

---

## Data model

### Candidate

Stores the current pipeline state:

| Column | Description |
|---|---|
| `id` | Primary key |
| `full_name` | Candidate's full name |
| `normalized_name` | Lowercased name for search |
| `current_stage` | Current pipeline stage |
| `current_stage_entered_at` | Timestamp of last stage change |
| `created_at` | Record creation timestamp |

### CandidateStageEvent

Stores the append-only audit history:

| Column | Description |
|---|---|
| `id` | Primary key |
| `candidate_id` | Foreign key to Candidate |
| `from_stage` | Previous stage (`null` for initial event) |
| `to_stage` | New stage |
| `occurred_at` | Timestamp of the transition |

The initial event has `from_stage = null` and `to_stage = APPLIED`.

A candidate's current stage and corresponding audit event are written in one transaction.

The following invariants are tested:

- `candidate.current_stage == latest_event.to_stage`
- `candidate.current_stage_entered_at == latest_event.occurred_at`

---

## Search architecture

Search uses a deterministic, domain-specific parser rather than unrestricted natural-language generation.

The processing flow is:

```
Raw query
→ normalization
→ phrase recognition
→ structured SearchPlan
→ validation
→ database filtering
→ RapidFuzz name scoring
→ intent-specific ranking
→ results and interpretation
```

Example structured plan:

```json
{
  "name": null,
  "current_stage": {
    "include": ["SCREENING"],
    "exclude": []
  },
  "current_stage_age": {
    "operator": "GT",
    "seconds": 604800
  },
  "history_predicates": [],
  "history_exclusions": []
}
```

The search response includes both a human-readable interpretation and the structured search plan used by the backend. This makes the search behavior explainable and easier to test.

### Search ranking

Ranking depends on the interpreted query:

| Query type | Ranking strategy |
|---|---|
| Name searches | Exact-match priority and fuzzy similarity |
| Time-in-stage searches | Longest-waiting candidate first |
| Historical movement searches | Most recent matching event first |
| General stage/exclusion searches | Stable alphabetical ordering |

Structured filters are always applied before fuzzy name ranking. A strong name match cannot bypass a stage or history condition.

### Valid zero-result search

A valid query with no matching candidates returns **200 OK** with an empty results list and the interpreted search plan.

### Invalid search

An unsupported or malformed query returns **422 Unprocessable Entity** with:

- Error code.
- Readable message.
- Offending fragment where available.
- Suggested corrections or examples.

---

## Architecture summary

```
React + TypeScript UI
        |
     HTTP/JSON
        |
    FastAPI API
        |
Candidate, Transition, and Search services
        |
    SQLAlchemy
        |
      SQLite
```

Responsibilities are separated as follows:

| Layer | Responsibility |
|---|---|
| API routes | HTTP input and output |
| Pydantic schemas | Request and response validation |
| Services | Business rules and application workflows |
| Search parser | Natural-language interpretation |
| SQLAlchemy models | Relational persistence |
| React components | User interface and interactions |

A modular monolith was chosen because the system is small, has one database, and must be easy for a reviewer to run locally.

---

## Key decisions and trade-offs

### Modular monolith instead of microservices

**Decision:** Use one backend application.

**Reason:** The candidate pipeline and search share the same data and transaction boundaries.

**Trade-off:** Components cannot be independently deployed, but microservices would add unnecessary networking, deployment, and consistency complexity for this assessment.

### SQLite instead of PostgreSQL

**Decision:** Use SQLite through SQLAlchemy.

**Reason:** Reviewers can run the project without configuring an external database.

**Trade-off:** SQLite has lower production concurrency and fewer advanced search capabilities. SQLAlchemy provides a migration path to PostgreSQL.

### Deterministic parser instead of LLM-only search

**Decision:** Convert supported natural-language phrases into a validated structured plan using deterministic rules.

**Reason:** The required search domain is small and explicitly described in the brief.

**Trade-off:** The parser supports a documented set of phrases rather than unrestricted natural language. In return, results are deterministic, explainable, inexpensive, and straightforward to test.

### RapidFuzz instead of a dedicated search service

**Decision:** Use RapidFuzz for candidate-name similarity.

**Reason:** The expected dataset is small, and a separate search engine would add infrastructure without providing meaningful assessment value.

**Trade-off:** Application-level fuzzy matching would not be suitable for a very large candidate dataset.

### Store both current state and history

**Decision:** Store the current stage on the candidate and all changes as separate audit events.

**Reason:** Current-stage grouping and filtering remain simple, while the event table preserves complete history.

**Trade-off:** The current stage is duplicated from the latest event. Transactional writes and invariant tests protect consistency.

### Transition buttons instead of drag and drop

**Decision:** Display only valid transition actions.

**Reason:** Buttons are accessible, quicker to implement, and communicate allowed transitions clearly.

**Trade-off:** The interface has less visual interaction than a drag-and-drop board, but carries lower implementation and validation risk.

---

## Assumptions

The following ambiguities were resolved explicitly:

- Hired and Rejected are terminal stages.
- A candidate may be rejected from Applied, Screening, Interview, or Offer.
- "Reached Offer but didn't get hired" means the candidate has an Offer history event and is not currently Hired. This includes candidates currently in Offer and candidates rejected after reaching Offer.
- "Since Monday" starts at 00:00 on the most recent Monday in the configured application timezone, inclusively.
- "More than a week" means more than exactly seven elapsed days.
- Full name is the only required candidate field.
- Duplicate names are permitted; the candidate ID is the unique identifier.
- The application manages exactly one job.
- Authentication and recruiter accounts are outside the assessment scope.
- Audit events do not record an actor because authentication is outside scope.
- Search supports the brief's English patterns and selected documented variations, not unrestricted natural language.
- Alphabetic text that does not match a filter is treated as a candidate-name query.
- A valid query with no matching candidates is not an error.
- Timestamps are stored in UTC, while relative calendar expressions are resolved using the configured application timezone.

---

## Known limitations

- No authentication or authorization.
- Supports only one job.
- Candidate records contain only names and pipeline information.
- Search supports a limited documented language rather than unrestricted natural language.
- Fuzzy matching occurs in application memory and is intended for small datasets.
- No pagination.
- No production database migrations.
- No email, interview scheduling, notes, CVs, or file attachments.
- No recruiter identity is stored on audit events.
- SQLite is suitable for the assessment but not the preferred choice for high-concurrency production use.

---

## What I would do with more time

- Add PostgreSQL and database migrations.
- Add authentication and recruiter authorization.
- Record the acting recruiter on every stage event.
- Add pagination and server-side fuzzy search.
- Expand the supported search grammar.
- Add fuzzy stage-term suggestions (e.g. `interveiw` → `Interview`).
- Add an optional LLM fallback that produces schema-validated search plans.
- Add candidate contact information and job-specific fields.
- Add accessibility testing and improved keyboard navigation.
- Add end-to-end browser tests.
- Add production logging, monitoring, backups, and deployment configuration.
- Add confirmation and undo workflows for selected non-audit actions while keeping existing history immutable.

---

## AI usage

AI tools were used as development assistants for:

- Reviewing the assessment requirements.
- Exploring architecture alternatives.
- Identifying business-rule edge cases.
- Reviewing the stage-transition design.
- Suggesting test scenarios.
- Reviewing search-parser behavior.
- Debugging failing tests.
- Improving documentation structure.

AI-generated recommendations were not accepted automatically. Suggested code and architecture were reviewed, tested, corrected, and simplified when they did not fit the requirements or assessment time limit.

The repository includes AI interaction logs in: `docs/ai-chat-log.md`

> Sensitive information and unrelated conversation should be removed before submission.

### A recommendation I disagreed with

One AI recommendation was to use an LLM for all natural-language search interpretation.

I chose not to follow that recommendation.

The assessment describes a small, well-defined search domain. A deterministic parser is more appropriate because it is:

- **Predictable.** Same input always produces the same output.
- **Testable.** Every supported pattern has a corresponding unit test.
- **Explainable.** The structured search plan is returned alongside results.
- **Available offline.** No external API dependency.
- **Free from API cost and latency.**
- **Less likely to invent unsupported filters.**
- **Easier to demonstrate** through a structured search plan.

An LLM could be introduced later as an optional fallback for unfamiliar wording. Its output would still need to conform to the same validated `SearchPlan` schema before being used to query the database.

This decision reflects a broader engineering principle: generative AI should be used where its flexibility creates enough value to justify its uncertainty and operational cost, not simply because the target role involves generative AI.

---

## API summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/candidates` | Create a candidate |
| `GET` | `/api/pipeline` | View candidates grouped by stage |
| `GET` | `/api/candidates/{candidate_id}` | Candidate details and history |
| `POST` | `/api/candidates/{candidate_id}/transitions` | Advance or reject a candidate |
| `GET` | `/api/search?q={query}` | Natural-language candidate search |

Interactive API documentation is available while the backend is running at: http://127.0.0.1:8000/docs

---

## Submission documents

| Document | Path |
|---|---|
| Architecture PDF | `docs/architecture.pdf` |
| Assumptions | `docs/assumptions.md` |
| AI logs | `docs/ai-chat-log.md` |

---

## Quick-start verification

Verify the commands from a clean environment:

**Terminal 1 (backend):**

```bash
cd backend
uv sync
uv run pytest -v
uv run python -m scripts.seed_demo_data
uv run uvicorn app.main:app --reload
```

**Terminal 2 (frontend):**

```bash
cd frontend
cp .env.example .env   # or Copy-Item .env.example .env on PowerShell
npm install
npm run build
npm run dev
```

Then open http://localhost:5173 in your browser.
