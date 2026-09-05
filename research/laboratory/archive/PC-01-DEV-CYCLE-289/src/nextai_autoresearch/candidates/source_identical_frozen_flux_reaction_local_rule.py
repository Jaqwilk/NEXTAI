from .factorized_flux_reaction_core import FactorizedFluxReaction


class Candidate(FactorizedFluxReaction):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="frozen")
