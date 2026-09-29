import type {
    PipelineCandidate,
    Stage,
  } from "../types/pipeline";
  import { STAGE_LABELS } from "../types/pipeline";
  
  interface StageColumnProps {
    stage: Stage;
    candidates: PipelineCandidate[];
    selectedCandidateId: number | null;
    selectionLocked: boolean;
    onCandidateSelect: (candidateId: number) => void;
  }
  
  function formatStageDuration(enteredAt: string): string {
    const enteredTime = new Date(enteredAt).getTime();
    const currentTime = Date.now();
  
    const elapsedMilliseconds = Math.max(
      0,
      currentTime - enteredTime,
    );
  
    const elapsedDays = Math.floor(
      elapsedMilliseconds / (1000 * 60 * 60 * 24),
    );
  
    if (elapsedDays === 0) {
      return "Entered today";
    }
  
    if (elapsedDays === 1) {
      return "1 day in stage";
    }
  
    return `${elapsedDays} days in stage`;
  }
  
  export function StageColumn({
    stage,
    candidates,
    selectedCandidateId,
    selectionLocked,
    onCandidateSelect,
  }: StageColumnProps) {
    return (
      <section className={`stage-column stage-${stage.toLowerCase()}`}>
        <header className="stage-column__header">
          <h2>{STAGE_LABELS[stage]}</h2>
          <span className="stage-column__count">
            {candidates.length}
          </span>
        </header>
  
        <div className="stage-column__candidates">
          {candidates.length === 0 ? (
            <p className="stage-column__empty">
              No candidates
            </p>
          ) : (
            candidates.map((candidate) => {
              const isSelected =
                selectedCandidateId === candidate.id;
            
              return (
                <button
                  className={`candidate-card${
                    isSelected ? " candidate-card--selected" : ""
                  }`}
                  key={candidate.id}
                  type="button"
                  onClick={() => onCandidateSelect(candidate.id)}
                  disabled={selectionLocked}
                  aria-pressed={isSelected}
                >
                  <span className="candidate-card__name">
                    {candidate.full_name}
                  </span>
            
                  <span className="candidate-card__duration">
                    {formatStageDuration(
                      candidate.current_stage_entered_at,
                    )}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </section>
    );
  }
  