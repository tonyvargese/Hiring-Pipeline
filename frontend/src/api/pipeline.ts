import type {
    CandidateCreateRequest,
    CandidateCreateResponse,
    PipelineResponse,
  } from "../types/pipeline";




const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getPipeline(): Promise<PipelineResponse> {
  const response = await fetch(`${API_BASE_URL}/api/pipeline`);

  if (!response.ok) {
    throw new Error(
      `Failed to load the pipeline. Status: ${response.status}`,
    );
  }

  return response.json() as Promise<PipelineResponse>;
}


export async function createCandidate(
    candidate: CandidateCreateRequest,
  ): Promise<CandidateCreateResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/candidates`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(candidate),
      },
    );
  
    if (!response.ok) {
      if (response.status === 422) {
        throw new Error(
          "Enter a valid candidate name between 1 and 150 characters.",
        );
      }
  
      throw new Error(
        `Failed to add candidate. Status: ${response.status}`,
      );
    }
  
    return response.json() as Promise<CandidateCreateResponse>;
  }