import { useCallback, useEffect, useRef, useState } from "react";

import { getCandidateDetails, getPipeline } from "./api/pipeline";
import "./App.css";
import { AddCandidateForm } from "./components/AddCandidateForm";
import { CandidateDetailsPanel } from "./components/CandidateDetailsPanel";
import { PipelineBoard } from "./components/PipelineBoard";
import {
  SearchPanel,
  type SearchPanelHandle,
} from "./components/SearchPanel";
import type { CandidateDetail, PipelineResponse } from "./types/pipeline";

function App() {
  const [pipeline, setPipeline] = useState<PipelineResponse | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<
    number | null
  >(null);
  const [selectedCandidate, setSelectedCandidate] =
    useState<CandidateDetail | null>(null);
  const [isDetailsLoading, setIsDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState<string | null>(
    null,
  );
  const [createPending, setCreatePending] = useState(false);
  const [transitionPending, setTransitionPending] = useState(false);
  const searchPanelRef = useRef<SearchPanelHandle>(null);

  const handleCreatePending = useCallback((pending: boolean) => {
    setCreatePending(pending);
  }, []);

  const handleTransitionPending = useCallback((pending: boolean) => {
    setTransitionPending(pending);
  }, []);

  const loadPipeline = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const pipelineData = await getPipeline();
      setPipeline(pipelineData);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "An unexpected error occurred.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadCandidateDetails = useCallback(
    async (candidateId: number) => {
      setSelectedCandidate((current) =>
        current?.id === candidateId ? current : null,
      );
      setSelectedCandidateId(candidateId);
      setIsDetailsLoading(true);
      setDetailsError(null);

      try {
        const candidate = await getCandidateDetails(candidateId);
        setSelectedCandidate(candidate);
      } catch (requestError) {
        const message =
          requestError instanceof Error
            ? requestError.message
            : "An unexpected error occurred.";

        setDetailsError(message);
        setSelectedCandidate((current) =>
          current?.id === candidateId ? current : null,
        );
      } finally {
        setIsDetailsLoading(false);
      }
    },
    [],
  );

  const refreshAfterChange = useCallback(async () => {
    await loadPipeline();
    searchPanelRef.current?.refresh();
  }, [loadPipeline]);

  const handleTransitionCompleted = useCallback(
    async (candidateId: number) => {
      await Promise.all([
        loadPipeline(),
        loadCandidateDetails(candidateId),
      ]);
      searchPanelRef.current?.refresh();
    },
    [loadPipeline, loadCandidateDetails],
  );

  const handleCloseDetails = useCallback(() => {
    setSelectedCandidateId(null);
    setSelectedCandidate(null);
    setDetailsError(null);
  }, []);

  useEffect(() => {
    let ignore = false;

    async function loadInitialPipeline() {
      try {
        const pipelineData = await getPipeline();

        if (!ignore) {
          setPipeline(pipelineData);
          setError(null);
        }
      } catch (requestError) {
        if (!ignore) {
          const message =
            requestError instanceof Error
              ? requestError.message
              : "An unexpected error occurred.";

          setError(message);
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    void loadInitialPipeline();

    return () => {
      ignore = true;
    };
  }, []);

  const mutationsLocked = createPending || transitionPending;

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-header__eyebrow">Recruitment workspace</p>
          <h1>Mini Hiring Pipeline</h1>
          <p className="app-header__description">
            Move candidates through each stage, then search the
            pipeline in plain language.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={() => void loadPipeline()}
          disabled={isLoading || mutationsLocked}
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      <AddCandidateForm
        onCandidateCreated={refreshAfterChange}
        actionsLocked={transitionPending}
        onPendingChange={handleCreatePending}
      />

      <SearchPanel
        ref={searchPanelRef}
        selectedCandidateId={selectedCandidateId}
        selectionLocked={transitionPending}
        onCandidateSelect={(candidateId) => {
          void loadCandidateDetails(candidateId);
        }}
      />

      {isLoading && pipeline === null ? (
        <section className="status-panel" role="status">
          <p>Loading pipeline...</p>
        </section>
      ) : null}

      {error ? (
        <section className="status-panel status-panel--error" role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => void loadPipeline()}>
            Try again
          </button>
        </section>
      ) : null}

      {isLoading && pipeline ? (
        <p className="inline-status" role="status">
          Updating pipeline...
        </p>
      ) : null}

      <div className="workspace">
        <div className="workspace__board">
          {pipeline ? (
            <PipelineBoard
              stages={pipeline.stages}
              selectedCandidateId={selectedCandidateId}
              selectionLocked={transitionPending}
              onCandidateSelect={(candidateId) => {
                void loadCandidateDetails(candidateId);
              }}
            />
          ) : null}
        </div>

        <CandidateDetailsPanel
          candidate={selectedCandidate}
          isLoading={isDetailsLoading}
          error={detailsError}
          actionsLocked={createPending}
          onClose={handleCloseDetails}
          onPendingChange={handleTransitionPending}
          onTransitionCompleted={handleTransitionCompleted}
        />
      </div>
    </main>
  );
}

export default App;
