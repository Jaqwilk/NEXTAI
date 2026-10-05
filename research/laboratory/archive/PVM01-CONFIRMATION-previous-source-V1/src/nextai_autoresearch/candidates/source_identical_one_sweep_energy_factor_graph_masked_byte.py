from .sparse_energy_factor_graph_core import Candidate as _Core


class Candidate(_Core):
    ROLE = "source_identical_one_sweep_energy_factor_graph_masked_byte"
    ONE_SWEEP = True
