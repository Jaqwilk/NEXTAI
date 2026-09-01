from .cross_family_shared_representation_v2 import (
    FAMILIES,
    PRIVILEGED,
    _derived_seeds,
    _run_cell,
    _training,
    run_suite,
)


BENCHMARK_VERSION = "cross_family_sparse_set_memory_v5"
CAUSAL_ROLES = (
    "shared_sparse_set_memory_v1",
    "independent_sparse_set_memory_v1",
    "source_identical_dense_set_attention_v1",
    "source_identical_frozen_sparse_router_v1",
)
ROLE_IMPLEMENTATION = {role: "sparse_set_memory_core_v1" for role in CAUSAL_ROLES}
ROLE_INTERVENTION = {
    CAUSAL_ROLES[0]: "pooled_sparse_learned_router",
    CAUSAL_ROLES[1]: "independent_sparse_learned_router",
    CAUSAL_ROLES[2]: "pooled_dense_learned_router",
    CAUSAL_ROLES[3]: "pooled_sparse_frozen_router",
}
