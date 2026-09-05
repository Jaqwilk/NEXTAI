from .shared_anonymous_prolongation_v1 import Candidate as _SharedCandidate


class Candidate(_SharedCandidate):
    pass


Candidate = _SharedCandidate

__all__ = ["Candidate"]
