import type { PipelineResponse } from "../types/pipeline";

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