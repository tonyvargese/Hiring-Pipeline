import type { PipelineStage } from "../types/pipeline";
import { StageColumn } from "./StageColumn";

interface PipelineBoardProps {
  stages: PipelineStage[];
  selectedCandidateId: number | null;
  selectionLocked: boolean;
  onCandidateSelect: (candidateId: number) => void;
}

export function PipelineBoard({
  stages,
  selectedCandidateId,
  selectionLocked,
  onCandidateSelect,
}: PipelineBoardProps) {
  return (
    <div className="pipeline-board">
      {stages.map((stageGroup) => (
        <StageColumn
          key={stageGroup.stage}
          stage={stageGroup.stage}
          candidates={stageGroup.candidates}
          selectedCandidateId={selectedCandidateId}
          selectionLocked={selectionLocked}
          onCandidateSelect={onCandidateSelect}
        />
      ))}
    </div>
  );
}