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


  export interface CandidateHistoryEvent {
    id: number;
    from_stage: Stage | null;
    to_stage: Stage;
    occurred_at: string;
  }
  
  export interface CandidateDetail {
    id: number;
    full_name: string;
    current_stage: Stage;
    current_stage_entered_at: string;
    current_stage_duration_seconds: number;
    created_at: string;
    allowed_next_stages: Stage[];
    history: CandidateHistoryEvent[];
  }
  
  export interface CandidateTransitionRequest {
    from_stage: Stage;
    to_stage: Stage;
  }
  
  export interface CandidateTransitionResponse {
  candidate: CandidateCreateResponse;
  event: CandidateHistoryEvent;
}

export type ComparisonOperator = "GT" | "GTE" | "LT" | "LTE";

export interface NameSearchCondition {
  text: string;
  fuzzy: boolean;
}

export interface CurrentStageCondition {
  include: Stage[];
  exclude: Stage[];
}

export interface StageAgeCondition {
  operator: ComparisonOperator;
  seconds: number;
}

export interface HistoryPredicate {
  stage: Stage;
  since: string | null;
  until: string | null;
}

export interface SearchPlan {
  name: NameSearchCondition | null;
  current_stage: CurrentStageCondition;
  current_stage_age: StageAgeCondition | null;
  history_predicates: HistoryPredicate[];
  history_exclusions: Stage[];
}

export interface SearchInterpretation {
  summary: string;
  corrections: string[];
}

export interface SearchCandidate {
  id: number;
  full_name: string;
  current_stage: Stage;
  current_stage_entered_at: string;
  score: number | null;
}

export interface SearchResponse {
  query: string;
  interpretation: SearchInterpretation;
  plan: SearchPlan;
  count: number;
  results: SearchCandidate[];
}