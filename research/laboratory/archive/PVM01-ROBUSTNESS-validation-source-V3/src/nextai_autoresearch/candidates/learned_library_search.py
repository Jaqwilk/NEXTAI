from nextai_autoresearch.program_search import ProgramSearchCandidate


class Candidate(ProgramSearchCandidate):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, "learned")
