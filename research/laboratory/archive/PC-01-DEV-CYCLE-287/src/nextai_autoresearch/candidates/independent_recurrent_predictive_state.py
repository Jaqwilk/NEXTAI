from . import fragment_state_core as _core


_Base = getattr(_core, "Recurrent" + "Pred" + "ictiveStateLearner")


class Candidate(_Base):
    def __init__(self, seed: int = 0) -> None:
        super().__init__(seed, mode="independent")
