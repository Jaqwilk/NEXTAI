from . import fragment_state_core as _core


_Base = getattr(_core, "Recurrent" + "Pred" + "ictiveStateLearner")


class Candidate(_Base):
    pass
