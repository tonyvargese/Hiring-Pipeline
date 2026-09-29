import type {
    PipelineCandidate,
    Stage,
  } from "../types/pipeline";
  import { STAGE_LABELS } from "../types/pipeline";
  
  interface StageColumnProps {
    stage: Stage;
    candidates: PipelineCandidate[];
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
            candidates.map((candidate) => (
              <article
                className="candidate-card"
                key={candidate.id}
              >
                <h3>{candidate.full_name}</h3>
  
                <p>
                  {formatStageDuration(
                    candidate.current_stage_entered_at,
                  )}
                </p>
              </article>
            ))
          )}
        </div>
      </section>
    );
  }
  