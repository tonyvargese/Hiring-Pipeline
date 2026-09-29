import {
    type FormEvent,
    useEffect,
    useRef,
    useState,
  } from "react";
  
  import { createCandidate } from "../api/pipeline";
  
  interface AddCandidateFormProps {
    onCandidateCreated: () => Promise<void>;
    actionsLocked: boolean;
    onPendingChange: (pending: boolean) => void;
  }
  
  export function AddCandidateForm({
    onCandidateCreated,
    actionsLocked,
    onPendingChange,
  }: AddCandidateFormProps) {
    const [fullName, setFullName] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] =
      useState<string | null>(null);
    const submitLock = useRef(false);

    useEffect(() => {
      onPendingChange(isSubmitting);
    }, [isSubmitting, onPendingChange]);
  
    async function handleSubmit(
      event: FormEvent<HTMLFormElement>,
    ) {
      event.preventDefault();

      if (submitLock.current || actionsLocked) {
        return;
      }
  
      const cleanedName = fullName.trim();
  
      if (!cleanedName) {
        setError("Candidate name is required.");
        return;
      }
  
      submitLock.current = true;
      setIsSubmitting(true);
      setError(null);
      setSuccessMessage(null);
  
      try {
        const candidate = await createCandidate({
          full_name: cleanedName,
        });
  
        setFullName("");
        setSuccessMessage(
          `${candidate.full_name} was added to Applied.`,
        );
  
        await onCandidateCreated();
      } catch (requestError) {
        const message =
          requestError instanceof Error
            ? requestError.message
            : "An unexpected error occurred.";
  
        setError(message);
      } finally {
        submitLock.current = false;
        setIsSubmitting(false);
      }
    }
  
    return (
      <section className="add-candidate-panel">
        <div>
          <h2>Add candidate</h2>
          <p>
            New candidates begin in the Applied stage.
          </p>
        </div>
  
        <div className="add-candidate-panel__form">
        <form
          className="add-candidate-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <label
            className="visually-hidden"
            htmlFor="candidate-name"
          >
            Candidate full name
          </label>
  
          <input
            id="candidate-name"
            name="fullName"
            type="text"
            value={fullName}
            onChange={(event) => {
              setFullName(event.target.value);
              setError(null);
              setSuccessMessage(null);
            }}
            placeholder="Candidate full name"
            autoComplete="name"
            maxLength={150}
            disabled={isSubmitting || actionsLocked}
          />
  
          <button
            className="primary-button"
            type="submit"
            disabled={
              isSubmitting || actionsLocked || !fullName.trim()
            }
          >
            {isSubmitting ? "Adding..." : "Add candidate"}
          </button>
        </form>
  
        {error ? (
          <p
            className="form-message form-message--error"
            role="alert"
          >
            {error}
          </p>
        ) : null}
  
        {successMessage ? (
          <p
            className="form-message form-message--success"
            role="status"
          >
            {successMessage}
          </p>
        ) : null}
        </div>
      </section>
    );
  }