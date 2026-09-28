class CandidateNotFoundError(Exception):
    def __init__(self, candidate_id: int) -> None:
        self.candidate_id = candidate_id
        super().__init__(f"Candidate {candidate_id} was not found.")

    
class SearchQueryError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        fragment: str | None = None,
        hints: list[str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.fragment = fragment
        self.hints = hints or []

        super().__init__(message)



