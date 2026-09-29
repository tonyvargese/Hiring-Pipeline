import type {
  CandidateCreateRequest,
  CandidateCreateResponse,
  CandidateDetail,
  CandidateTransitionRequest,
  CandidateTransitionResponse,
  PipelineResponse,
  SearchResponse,
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


  interface ApiErrorResponse {
    detail?: {
      code?: string;
      message?: string;
      hints?: string[];
    };
  }
  
  async function getApiError(
    response: Response,
    fallbackMessage: string,
  ): Promise<string> {
    try {
      const errorData =
        (await response.json()) as ApiErrorResponse;
  
      if (errorData.detail?.message) {
        const hints = errorData.detail.hints ?? [];
  
        return hints.length > 0
          ? `${errorData.detail.message} ${hints.join(" ")}`
          : errorData.detail.message;
      }
    } catch {
      // Fall back when the response is not JSON.
    }
  
    return fallbackMessage;
  }



  export async function getCandidateDetails(
    candidateId: number,
  ): Promise<CandidateDetail> {
    const response = await fetch(
      `${API_BASE_URL}/api/candidates/${candidateId}`,
    );
  
    if (!response.ok) {
      throw new Error(
        await getApiError(
          response,
          `Failed to load candidate. Status: ${response.status}`,
        ),
      );
    }
  
    return response.json() as Promise<CandidateDetail>;
  }


  export async function transitionCandidate(
    candidateId: number,
    transition: CandidateTransitionRequest,
  ): Promise<CandidateTransitionResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/candidates/${candidateId}/transitions`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(transition),
      },
    );
  
    if (!response.ok) {
      throw new Error(
        await getApiError(
          response,
          `Failed to move candidate. Status: ${response.status}`,
        ),
      );
    }
  
    return response.json() as Promise<CandidateTransitionResponse>;
  }

export class InvalidSearchQueryError extends Error {
  readonly code: string;
  readonly fragment: string | null;
  readonly hints: string[];

  constructor(
    code: string,
    message: string,
    fragment: string | null,
    hints: string[],
  ) {
    super(message);
    this.name = "InvalidSearchQueryError";
    this.code = code;
    this.fragment = fragment;
    this.hints = hints;
  }
}

interface SearchErrorBody {
  detail?:
    | {
        code?: string;
        message?: string;
        fragment?: string | null;
        hints?: string[];
      }
    | Array<{ msg?: string }>;
}

async function readInvalidSearchError(
  response: Response,
): Promise<InvalidSearchQueryError> {
  try {
    const data = (await response.json()) as SearchErrorBody;
    const detail = data.detail;

    if (detail && !Array.isArray(detail) && detail.message) {
      return new InvalidSearchQueryError(
        detail.code ?? "INVALID_SEARCH_QUERY",
        detail.message,
        detail.fragment ?? null,
        detail.hints ?? [],
      );
    }

    if (Array.isArray(detail)) {
      const message = detail
        .map((item) => item.msg)
        .filter((msg): msg is string => Boolean(msg))
        .join(" ");

      return new InvalidSearchQueryError(
        "INVALID_SEARCH_QUERY",
        message || "The search query is not valid.",
        null,
        ["Enter a candidate name or a supported filter."],
      );
    }
  } catch {
    // Fall back when the response is not JSON.
  }

  return new InvalidSearchQueryError(
    "INVALID_SEARCH_QUERY",
    "The search query could not be understood.",
    null,
    [
      "Try a candidate name.",
      "Try 'in Interview right now'.",
      "Try 'Screening for more than a week'.",
    ],
  );
}

export async function searchCandidates(
  query: string,
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  const response = await fetch(
    `${API_BASE_URL}/api/search?${params.toString()}`,
  );

  if (!response.ok) {
    if (response.status === 422) {
      throw await readInvalidSearchError(response);
    }

    throw new Error(
      await getApiError(
        response,
        `Search failed. Status: ${response.status}`,
      ),
    );
  }

  return response.json() as Promise<SearchResponse>;
}



