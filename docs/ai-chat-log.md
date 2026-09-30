# AI Chat Log

## Project

**Mini Hiring Pipeline**  
**Repository:** https://github.com/tonyvargese/Hiring-Pipeline

## Purpose of this document

AI tools were used as development assistants during this take-home assessment. AI output was reviewed, tested, corrected, and adapted rather than accepted automatically.

This document records the main areas where AI was used, important recommendations, corrections made during implementation, and one significant architectural recommendation that I chose not to follow.

## How AI was used

AI assistance was used for:

- Extracting requirements and business rules from the assessment brief.
- Reviewing architecture options and identifying unnecessary complexity.
- Designing the candidate and stage-event data model.
- Defining valid and invalid stage transitions.
- Designing append-only audit history.
- Designing a structured natural-language search plan.
- Identifying edge cases for relative dates and historical-stage queries.
- Suggesting backend and frontend test scenarios.
- Debugging failing tests during implementation.
- Structuring the README, assumptions, and architecture documentation.

AI was not used as an unchecked source of truth. Suggestions were compared with the brief, simplified to fit the time limit, and verified through automated tests and manual use.

## Main AI-assisted design discussions

### 1. Architecture scope

**Prompt/theme:** Design a practical architecture for one developer within the assessment deadline.

**AI recommendation used:** Build a modular monolith with a React frontend, FastAPI backend, SQLAlchemy, and SQLite.

**Reason accepted:** The application has one recruiter, one job, one database, and closely related business rules. Microservices and separate search infrastructure would add deployment and consistency complexity without helping the assessment.

### 2. Candidate state and audit history

**Prompt/theme:** Model current pipeline state while preserving a complete immutable history.

**AI recommendation used:** Store the candidate's current stage for simple board queries and store every stage entry as a separate event.

**Implementation decision:** Candidate creation writes both the Candidate row and the initial APPLIED event in one transaction. Every successful transition updates the candidate and appends an event using the same timestamp.

**Important invariant:**

```text
candidate.current_stage == latest_event.to_stage
candidate.current_stage_entered_at == latest_event.occurred_at
```

### 3. Stage-transition safety

**Prompt/theme:** Prevent stage skipping, terminal-state reversal, and accidental double advancement.

**Initial design discussion:** A version column and optimistic locking were considered.

**Final decision:** The request contains both `from_stage` and `to_stage`. The backend performs a conditional update only when the stored current stage still equals `from_stage`.

**Reason:** This directly protects the practical stale-request and double-click case without adding a separate version field.

### 4. Search architecture

**Prompt/theme:** Support the natural-language examples in the brief while keeping results explainable.

**AI recommendation used:** Parse supported phrases into a validated structured `SearchPlan`, then execute database filters and apply RapidFuzz only to candidate names.

**Search flow:**

```text
Raw query
-> normalization
-> phrase recognition
-> structured SearchPlan
-> validation
-> database filtering
-> fuzzy name scoring
-> intent-specific ranking
-> interpretation and results
```

The API returns the structured plan so the reviewer can see exactly how a query was interpreted.

### 5. Demo data

**Prompt/theme:** Ensure all required search examples produce meaningful results in the walkthrough.

**AI/reviewer recommendation used:** Create deterministic backdated seed data rather than creating all transitions at the current time.

**Reason:** Without backdated events, searches such as "stuck in Screening for more than a week" would return no results during the demo.

## One recommendation I disagreed with

An AI recommendation was to use an LLM for all natural-language search interpretation.

I chose not to follow that recommendation.

The search domain in the assessment is small and well defined. A deterministic parser is more appropriate because it is:

- Predictable.
- Testable.
- Explainable.
- Available offline.
- Free from API cost and latency.
- Less likely to invent unsupported filters.
- Easier to demonstrate through a structured search plan.

An LLM could be added later as an optional fallback for unfamiliar wording. Any LLM output would still need to conform to the validated `SearchPlan` schema before it could influence a database query.

This was a deliberate decision not to use generative AI where deterministic software provides a safer and simpler solution.

## Examples where AI output was corrected

### Duplicate exception classes

A candidate-details test failed because two modules defined separate `CandidateNotFoundError` classes with the same name. The exception raised by the service was therefore not caught by the API route.

**Correction:** Define the exception once in `app/errors.py` and import the shared class everywhere.

### Stale transition validation order

A repeated transition returned `INVALID_STAGE_TRANSITION` instead of `STALE_STAGE_TRANSITION` because allowed transitions were checked before comparing the request's `from_stage` with the stored current stage.

**Correction:** Check for a stale starting stage first, then validate the requested destination.

### Unintended name condition

The query:

```text
Who has been stuck in Screening for more than a week?
```

initially produced the correct stage and duration filters but also incorrectly treated `has been` as a candidate name. This caused the search to return zero results.

**Correction:** Remove recognized filler words before applying the alphabetic name fallback, and add a parser assertion that `plan.name` is `null` for this query.

### Name-plan assignment typo

A parser implementation created a local variable named `planname` instead of assigning the name condition to `plan.name`.

**Correction:** Assign the condition to the structured plan and rerun focused and full test suites.

## Validation performed

AI-assisted code and decisions were validated through:

- Unit tests for allowed and invalid transitions.
- Tests for terminal Hired and Rejected stages.
- Stale transition tests.
- Candidate/history consistency checks.
- Table-driven parser tests for the required search examples.
- Search API integration tests.
- Valid zero-result and invalid-query tests.
- Frontend lint and production build checks.
- Manual verification through FastAPI Swagger and the React interface.

## Limitations of AI assistance

AI suggestions sometimes introduced:

- More layers than the small application required.
- Fields that were later removed, such as a version and event sequence number.
- Code defects that were caught by tests.
- Recommendations that did not fully match the assessment time limit.

For that reason, the assessment brief remained the source of truth, and automated tests were treated as essential evidence rather than assuming generated code was correct.

## Full conversation record

This file is a curated engineering log of the relevant AI-assisted work. If the evaluator expects the complete raw transcript, an exported or copied transcript should also be added under `docs/ai-chat-transcript/` or linked from this section after removing unrelated or sensitive information.
