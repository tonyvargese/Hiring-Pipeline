export type Stage =
  | "APPLIED"
  | "SCREENING"
  | "INTERVIEW"
  | "OFFER"
  | "HIRED"
  | "REJECTED";

export interface PipelineCandidate {
  id: number;
  full_name: string;
  current_stage: Stage;
  current_stage_entered_at: string;
}

export interface PipelineStage {
  stage: Stage;
  candidates: PipelineCandidate[];
}

export interface PipelineResponse {
  stages: PipelineStage[];
}

export const STAGE_LABELS: Record<Stage, string> = {
  APPLIED: "Applied",
  SCREENING: "Screening",
  INTERVIEW: "Interview",
  OFFER: "Offer",
  HIRED: "Hired",
  REJECTED: "Rejected",
};

export interface CandidateCreateRequest {
    full_name: string;
  }
  
  export interface CandidateCreateResponse {
    id: number;
    full_name: string;
    current_stage: Stage;
    current_stage_entered_at: string;
    created_at: string;
  }