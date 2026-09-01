from .wt_particle_proposal_predictive_state_core_v1 import Candidate as _Candidate


class Candidate(_Candidate):
    mode = "deterministic_posterior_mean"
