import {
  type FormEvent,
  type Ref,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import {
  InvalidSearchQueryError,
  searchCandidates,
} from "../api/pipeline";
import type {
  ComparisonOperator,
  HistoryPredicate,
  SearchPlan,
  SearchResponse,
} from "../types/pipeline";
import { STAGE_LABELS } from "../types/pipeline";

export interface SearchPanelHandle {
  refresh: () => void;
}

interface SearchPanelProps {
  selectedCandidateId: number | null;
  selectionLocked: boolean;
  onCandidateSelect: (candidateId: number) => void;
  ref?: Ref<SearchPanelHandle>;
}

interface QueuedSearch {
  query: string;
  preserveResults: boolean;
}

const EXAMPLE_QUERIES = [
  "Find Priya Sharam",
  "Who's in Interview right now?",
  "Who has been stuck in Screening for more than a week?",
  "Who reached the Offer stage but didn't get hired?",
];

const OPERATOR_LABELS: Record<ComparisonOperator, string> = {
  GT: "greater than",
  GTE: "at least",
  LT: "less than",
  LTE: "at most",
};

function formatTimestamp(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatAge(seconds: number): string {
  if (seconds % 86400 === 0) {
    const days = seconds / 86400;
    return `${days} day${days === 1 ? "" : "s"}`;
  }

  if (seconds % 3600 === 0) {
    const hours = seconds / 3600;
    return `${hours} hour${hours === 1 ? "" : "s"}`;
  }

  return `${seconds} seconds`;
}

function describeHistoryPredicate(
  predicate: HistoryPredicate,
): string {
  const since = formatTimestamp(predicate.since);
  const until = formatTimestamp(predicate.until);
  let description = `Entered ${STAGE_LABELS[predicate.stage]}`;

  if (since) {
    description += ` since ${since}`;
  }

  if (until) {
    description += ` until ${until}`;
  }

  return description;
}

function describePlan(
  plan: SearchPlan,
): Array<{ label: string; value: string }> {
  const age = plan.current_stage_age;

  return [
    {
      label: "Name",
      value: plan.name
        ? `"${plan.name.text}" (${plan.name.fuzzy ? "fuzzy" : "exact"})`
        : "Not used",
    },
    {
      label: "Include current stages",
      value:
        plan.current_stage.include.length > 0
          ? plan.current_stage.include
              .map((stage) => STAGE_LABELS[stage])
              .join(", ")
          : "Any stage",
    },
    {
      label: "Exclude current stages",
      value:
        plan.current_stage.exclude.length > 0
          ? plan.current_stage.exclude
              .map((stage) => STAGE_LABELS[stage])
              .join(", ")
          : "None",
    },
    {
      label: "Time in current stage",
      value: age
        ? `${OPERATOR_LABELS[age.operator]} ${formatAge(age.seconds)}`
        : "Not used",
    },
    {
      label: "History must include",
      value:
        plan.history_predicates.length > 0
          ? plan.history_predicates
              .map(describeHistoryPredicate)
              .join("; ")
          : "Not used",
    },
    {
      label: "History must exclude",
      value:
        plan.history_exclusions.length > 0
          ? plan.history_exclusions
              .map((stage) => STAGE_LABELS[stage])
              .join(", ")
          : "None",
    },
  ];
}

export function SearchPanel({
  selectedCandidateId,
  selectionLocked,
  onCandidateSelect,
  ref,
}: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [queryError, setQueryError] =
    useState<InvalidSearchQueryError | null>(null);
  const [requestError, setRequestError] = useState<string | null>(
    null,
  );

  const inFlight = useRef(false);
  const submittedQueryRef = useRef<string | null>(null);
  const queuedSearch = useRef<QueuedSearch | null>(null);
  const executeSearchRef = useRef<
    (
      rawQuery: string,
      options?: { preserveResults?: boolean },
    ) => Promise<void>
  >(async () => undefined);

  const executeSearch = useCallback(
    async (
      rawQuery: string,
      options?: { preserveResults?: boolean },
    ) => {
      const cleanedQuery = rawQuery.trim();
      const preserveResults = options?.preserveResults ?? false;

      if (!cleanedQuery) {
        setQueryError(null);
        setRequestError("Enter a search query.");
        return;
      }

      if (inFlight.current) {
        const isDuplicateClick =
          !preserveResults &&
          cleanedQuery === submittedQueryRef.current;

        if (!isDuplicateClick) {
          queuedSearch.current = {
            query: cleanedQuery,
            preserveResults,
          };
        }

        return;
      }

      inFlight.current = true;
      submittedQueryRef.current = cleanedQuery;
      setQuery(cleanedQuery);
      setIsSearching(true);
      setQueryError(null);
      setRequestError(null);

      if (!preserveResults) {
        setResult(null);
      }

      try {
        const data = await searchCandidates(cleanedQuery);
        setResult(data);
      } catch (error) {
        if (error instanceof InvalidSearchQueryError) {
          setResult(null);
          setQueryError(error);
        } else {
          if (!preserveResults) {
            setResult(null);
          }

          setRequestError(
            error instanceof Error
              ? error.message
              : "Search failed.",
          );
        }
      } finally {
        inFlight.current = false;
        setIsSearching(false);

        const queued = queuedSearch.current;
        queuedSearch.current = null;

        if (queued) {
          void executeSearchRef.current(queued.query, {
            preserveResults: queued.preserveResults,
          });
        }
      }
    },
    [],
  );

  useEffect(() => {
    executeSearchRef.current = executeSearch;
  }, [executeSearch]);

  useImperativeHandle(
    ref,
    () => ({
      refresh() {
        const queryToRefresh = submittedQueryRef.current;

        if (!queryToRefresh) {
          return;
        }

        void executeSearchRef.current(queryToRefresh, {
          preserveResults: true,
        });
      },
    }),
    [],
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void executeSearch(query);
  }

  const planRows = result ? describePlan(result.plan) : [];

  return (
    <section className="search-panel" aria-label="Candidate search">
      <div className="search-panel__intro">
        <h2>Search candidates</h2>
        <p>
          Ask in plain language. Each search shows the interpretation,
          structured plan, corrections, and ranked matches.
        </p>
      </div>

      <form className="search-form" onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="candidate-search">
          Search candidates
        </label>

        <input
          id="candidate-search"
          name="query"
          type="search"
          value={query}
          maxLength={300}
          placeholder="Search by name or stage"
          disabled={isSearching}
          onChange={(event) => {
            setQuery(event.target.value);
            setRequestError(null);
          }}
        />

        <button
          className="primary-button"
          type="submit"
          disabled={isSearching || !query.trim()}
        >
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="search-examples">
        {EXAMPLE_QUERIES.map((example) => (
          <button
            key={example}
            className="example-chip"
            type="button"
            disabled={isSearching}
            onClick={() => {
              setQuery(example);
              void executeSearch(example);
            }}
          >
            {example}
          </button>
        ))}
      </div>

      {isSearching ? (
        <p className="search-panel__status" role="status">
          Searching...
        </p>
      ) : null}

      {requestError ? (
        <p className="form-message form-message--error" role="alert">
          {requestError}
        </p>
      ) : null}

      {queryError ? (
        <div className="query-error" role="alert">
          <h3>Invalid search</h3>
          <p>{queryError.message}</p>
          <p className="query-error__code">Code: {queryError.code}</p>

          {queryError.fragment ? (
            <p>
              Unrecognized text:{" "}
              <span className="query-error__fragment">
                {queryError.fragment}
              </span>
            </p>
          ) : null}

          {queryError.hints.length > 0 ? (
            <>
              <p className="query-error__hints-label">Try instead:</p>
              <ul>
                {queryError.hints.map((hint) => (
                  <li key={hint}>{hint}</li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}

      {result ? (
        <div className="search-explanation" aria-live="polite">
          <section>
            <h3>Search interpretation</h3>
            <p className="search-explanation__query">
              Query: “{result.query}”
            </p>
            <p>{result.interpretation.summary}</p>
          </section>

          <section>
            <h3>Corrections</h3>
            {result.interpretation.corrections.length === 0 ? (
              <p>No corrections were applied.</p>
            ) : (
              <ul className="correction-list">
                {result.interpretation.corrections.map(
                  (correction, index) => (
                    <li key={`${index}-${correction}`}>
                      {correction}
                    </li>
                  ),
                )}
              </ul>
            )}
          </section>

          <section>
            <h3>Structured plan</h3>
            <dl className="plan-list">
              {planRows.map((row) => (
                <div key={row.label}>
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section>
            <h3>
              Ranked results ({result.count})
            </h3>

            {result.results.length === 0 ? (
              <p>No candidates matched this search.</p>
            ) : (
              <ol className="result-list">
                {result.results.map((candidate, index) => {
                  const isSelected =
                    selectedCandidateId === candidate.id;

                  return (
                    <li key={candidate.id}>
                      <button
                        className={`result-card${
                          isSelected ? " result-card--selected" : ""
                        }`}
                        type="button"
                        disabled={selectionLocked}
                        aria-pressed={isSelected}
                        onClick={() =>
                          onCandidateSelect(candidate.id)
                        }
                      >
                        <span className="result-card__rank">
                          {index + 1}
                        </span>
                        <span className="result-card__name">
                          {candidate.full_name}
                        </span>
                        <span
                          className={`stage-badge stage-badge--${candidate.current_stage.toLowerCase()}`}
                        >
                          {STAGE_LABELS[candidate.current_stage]}
                        </span>
                        <span className="result-card__score">
                          {candidate.score === null
                            ? "Filter rank"
                            : `Score ${Math.round(candidate.score)}`}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ol>
            )}
          </section>
        </div>
      ) : null}
    </section>
  );
}
