from .sparse_energy_factor_graph_core import Candidate as _Core


class Candidate(_Core):
    ROLE = "source_identical_frozen_energy_factor_graph_masked_byte"
    LEARN_FACTORS = False
