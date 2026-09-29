import type { PipelineStage } from "../types/pipeline";
import { StageColumn } from "./StageColumn";

interface PipelineBoardProps {
  stages: PipelineStage[];
}

export function PipelineBoard({
  stages,
}: PipelineBoardProps) {
  return (
    <div className="pipeline-board">
      {stages.map((stageGroup) => (
        <StageColumn
          key={stageGroup.stage}
          stage={stageGroup.stage}
          candidates={stageGroup.candidates}
        />
      ))}
    </div>
  );
}