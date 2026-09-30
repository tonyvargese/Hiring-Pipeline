# Assumptions

The assessment brief is the source of truth for this project. The following
assumptions document behavior that was not fully specified in the brief.

## 1. One job

The application manages candidates for exactly one job.

A jobs table, job-selection interface, and candidates assigned to multiple jobs
are outside the scope of this assessment.

## 2. Candidate information

A candidate's full name is the only required personal field.

Email addresses, phone numbers, CVs, interview notes, and other candidate
information were not specified in the brief and are therefore not included.

## 3. Duplicate names

Multiple candidates may have the same full name.

A candidate's database ID, rather than the name, is the unique identifier.

## 4. Initial stage

Every newly created candidate starts in the `APPLIED` stage.

Candidate creation also records an initial audit event with:

- `from_stage = null`
- `to_stage = APPLIED`

## 5. Final stages

Both `HIRED` and `REJECTED` are terminal stages.

Candidates cannot leave either final stage. This interpretation follows the
requirement that reversing a final outcome should not be possible.

## 6. Rejection

A candidate may be rejected from:

- `APPLIED`
- `SCREENING`
- `INTERVIEW`
- `OFFER`

A candidate cannot be rejected after reaching `HIRED`.

## 7. One-stage advancement

Normal progression can advance by only one stage at a time:

```text
APPLIED -> SCREENING
SCREENING -> INTERVIEW
INTERVIEW -> OFFER
OFFER -> HIRED