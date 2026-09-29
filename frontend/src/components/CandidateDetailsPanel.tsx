import { useEffect, useRef, useState } from "react";

import { transitionCandidate } from "../api/pipeline";
import type {
  CandidateDetail,
  Stage,
} from "../types/pipeline";
import { STAGE_LABELS } from "../types/pipeline";

interface CandidateDetailsPanelProps {
  candidate: CandidateDetail | null;
  isLoading: boolean;
  error: string | null;
  actionsLocked: boolean;
  onClose: () => void;
  onPendingChange: (pending: boolean) => void;
  onTransitionCompleted: (
    candidateId: number,
  ) => Promise<void>;
}

function formatDuration(totalSeconds: number): string {
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor(
    (totalSeconds % 86400) / 3600,
  );
  const minutes = Math.floor(
    (totalSeconds % 3600) / 60,
  );

  if (days > 0) {
    return `${days} day${days === 1 ? "" : "s"}, ${hours} hour${
      hours === 1 ? "" : "s"
    }`;
  }

  if (hours > 0) {
    return `${hours} hour${hours === 1 ? "" : "s"}, ${minutes} minute${
      minutes === 1 ? "" : "s"
    }`;
  }

  if (minutes === 0) {
    return "Less than a minute";
  }

  return `${minutes} minute${minutes === 1 ? "" : "s"}`;
}

function formatDateTime(timestamp: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

function getEventLabel(
  fromStage: Stage | null,
  toStage: Stage,
): string {
  if (fromStage === null) {
    return `Added to ${STAGE_LABELS[toStage]}`;
  }

  if (toStage === "REJECTED") {
    return `Rejected from ${STAGE_LABELS[fromStage]}`;
  }

  return `${STAGE_LABELS[fromStage]} → ${STAGE_LABELS[toStage]}`;
}

export function CandidateDetailsPanel({
  candidate,
  isLoading,
  error,
  actionsLocked,
  onClose,
  onPendingChange,
  onTransitionCompleted,
}: CandidateDetailsPanelProps) {
  const [transitioningTo, setTransitioningTo] =
    useState<Stage | null>(null);

  const [transitionError, setTransitionError] =
    useState<string | null>(null);

  const transitionLock = useRef(false);
  const actionsDisabled =
    transitioningTo !== null || actionsLocked || isLoading;

  useEffect(() => {
    onPendingChange(transitioningTo !== null);
  }, [transitioningTo, onPendingChange]);

  async function handleTransition(
    toStage: Stage,
  ): Promise<void> {
    if (
      !candidate ||
      transitionLock.current ||
      actionsLocked ||
      isLoading
    ) {
      return;
    }

    transitionLock.current = true;
    setTransitioningTo(toStage);
    setTransitionError(null);

    try {
      await transitionCandidate(candidate.id, {
        from_stage: candidate.current_stage,
        to_stage: toStage,
      });

      await onTransitionCompleted(candidate.id);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "An unexpected transition error occurred.";

      setTransitionError(message);
    } finally {
      transitionLock.current = false;
      setTransitioningTo(null);
    }
  }

  return (
    <aside
      className="candidate-details"
      aria-label="Candidate details"
    >
      <div className="candidate-details__header">
        <div>
          <p className="candidate-details__eyebrow">
            Candidate details
          </p>

          <h2>
            {candidate?.full_name ?? "Select a candidate"}
          </h2>
        </div>

        {candidate ? (
          <button
            className="icon-button"
            type="button"
            onClick={onClose}
            disabled={transitioningTo !== null}
            aria-label="Close candidate details"
          >
            ×
          </button>
        ) : null}
      </div>

      {isLoading && !candidate ? (
        <p className="candidate-details__status" role="status">
          Loading candidate...
        </p>
      ) : null}

      {isLoading && candidate ? (
        <p className="candidate-details__status" role="status">
          Refreshing details...
        </p>
      ) : null}

      {error ? (
        <p
          className="form-message form-message--error"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {!candidate && !isLoading && !error ? (
        <p className="candidate-details__empty">
          Select a candidate card to see stage history and
          available actions.
        </p>
      ) : null}

      {candidate ? (
        <>
          <dl className="candidate-summary">
            <div>
              <dt>Current stage</dt>
              <dd>
                <span
                  className={`stage-badge stage-badge--${candidate.current_stage.toLowerCase()}`}
                >
                  {STAGE_LABELS[candidate.current_stage]}
                </span>
              </dd>
            </div>

            <div>
              <dt>Time in current stage</dt>
              <dd>
                {formatDuration(
                  candidate.current_stage_duration_seconds,
                )}
              </dd>
            </div>

            <div>
              <dt>Entered current stage</dt>
              <dd>
                {formatDateTime(
                  candidate.current_stage_entered_at,
                )}
              </dd>
            </div>
          </dl>

          <section className="candidate-actions">
            <h3>Available actions</h3>

            {candidate.allowed_next_stages.length === 0 ? (
              <p className="candidate-actions__terminal">
                This candidate is in a final stage.
              </p>
            ) : (
              <div className="candidate-actions__buttons">
                {[...candidate.allowed_next_stages]
                  .sort((left, right) => {
                    if (left === "REJECTED") {
                      return 1;
                    }

                    if (right === "REJECTED") {
                      return -1;
                    }

                    return left.localeCompare(right);
                  })
                  .map((nextStage) => {
                    const isReject =
                      nextStage === "REJECTED";

                    return (
                      <button
                        className={
                          isReject
                            ? "danger-button"
                            : "primary-button"
                        }
                        key={nextStage}
                        type="button"
                        disabled={actionsDisabled}
                        onClick={() =>
                          void handleTransition(nextStage)
                        }
                      >
                        {transitioningTo === nextStage
                          ? "Updating..."
                          : isReject
                            ? "Reject candidate"
                            : `Move to ${STAGE_LABELS[nextStage]}`}
                      </button>
                    );
                  })}
              </div>
            )}

            {transitionError ? (
              <p
                className="form-message form-message--error"
                role="alert"
              >
                {transitionError}
              </p>
            ) : null}
          </section>

          <section className="candidate-history">
            <h3>
              Complete stage history ({candidate.history.length})
            </h3>

            <ol className="history-list">
              {candidate.history.map((event) => (
                  <li
                    className="history-item"
                    key={event.id}
                  >
                    <span className="history-item__marker" />

                    <div>
                      <strong>
                        {getEventLabel(
                          event.from_stage,
                          event.to_stage,
                        )}
                      </strong>

                      <time dateTime={event.occurred_at}>
                        {formatDateTime(event.occurred_at)}
                      </time>
                    </div>
                  </li>
                ))}
            </ol>
          </section>
        </>
      ) : null}
    </aside>
  );
}