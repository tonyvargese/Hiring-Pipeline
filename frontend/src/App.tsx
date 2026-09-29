import { useCallback, useEffect, useState } from "react";

import { getPipeline } from "./api/pipeline";
import "./App.css";
import { PipelineBoard } from "./components/PipelineBoard";
import type { PipelineResponse } from "./types/pipeline";

function App() {
  const [pipeline, setPipeline] =
    useState<PipelineResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    void loadPipeline();
  }, [loadPipeline]);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-header__eyebrow">
            Recruitment workspace
          </p>

          <h1>Mini Hiring Pipeline</h1>

          <p className="app-header__description">
            Manage candidates and track every stage change.
          </p>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={() => void loadPipeline()}
          disabled={isLoading}
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {isLoading && pipeline === null ? (
        <section className="status-panel">
          <p>Loading pipeline...</p>
        </section>
      ) : null}

      {error ? (
        <section className="status-panel status-panel--error">
          <p>{error}</p>

          <button
            type="button"
            onClick={() => void loadPipeline()}
          >
            Try again
          </button>
        </section>
      ) : null}

      {pipeline ? (
        <PipelineBoard stages={pipeline.stages} />
      ) : null}
    </main>
  );
}

export default App;
``