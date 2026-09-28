class CandidateNotFoundError(Exception):
    def __init__(self, candidate_id: int) -> None:
        self.candidate_id = candidate_id
        super().__init__(f"Candidate {candidate_id} was not found.")
