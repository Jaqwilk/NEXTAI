from __future__ import annotations

from typing import Any

from .base import CandidateBase, CandidateMetadata
from .contextual_chow_liu import Candidate as Contextual
from .empirical_autoregressive_table import Candidate as Autoregressive
from .empirical_joint_table import Candidate as Joint
from .exact_finite_state_propagation import Candidate as ExactLocal
from .cssr_state_reconstructor import Candidate as CSSR
from .oracle_context_spn import Candidate as OracleProbabilistic
from .oracle_local_state_rule import Candidate as OracleLocal
from .oracle_predictive_state import Candidate as OraclePredictive
from .oracle_conjugacy_library import Candidate as OracleProgram
from .relational_graph_mdl_library import Candidate as RelationalProgram
from nextai_autoresearch.cross_family_transfer_v2_contract import (
    PrivilegedQuery, PrivilegedTraining, PrivilegedUpdate,
)


def _number(model: Any, name: str, default: float = 0.0) -> float:
    value = getattr(model, name, default)
    return float(value() if callable(value) else value)


class SpecialistSuiteV2(CandidateBase):
    metadata = CandidateMetadata(
        "cross-family-specialist-suite-v2", "specialist_control",
        "Summed native specialists across all four frozen world families.",
    )

    def __init__(self, seed: int = 0, probability_mode: str = "contextual") -> None:
        super().__init__(seed)
        self.probability_mode = probability_mode
        self.models: dict[int, Any] = {}
        self.families: dict[int, str] = {}
        self.oracle_roles: dict[int, tuple[int, ...]] = {}
        self.memo: dict[tuple[int, tuple[int, ...]], tuple[float, ...]] = {}
        self.last_bytes_touched = self.meta_fit_ops = 0.0

    def _model(self, family: str):
        oracle = self.probability_mode == "oracle"
        if family == "probabilistic":
            cls = OracleProbabilistic if oracle else {
                "contextual": Contextual, "joint": Joint,
                "autoregressive": Autoregressive,
            }[self.probability_mode]
        elif family == "predictive":
            cls = OraclePredictive if oracle else CSSR
        elif family == "local":
            cls = OracleLocal if oracle else ExactLocal
        else:
            cls = OracleProgram if oracle else RelationalProgram
        return cls(seed=self.seed)

    def fit(self, facts: PrivilegedTraining, universe_size: int, max_depth: int) -> None:
        if not isinstance(facts, PrivilegedTraining):
            raise TypeError("specialist suite requires its privileged envelope")
        self.models, self.families, self.oracle_roles, self.memo = {}, {}, {}, {}
        self.fit_ops = 0.0
        for world in facts.native_worlds:
            model = self._model(world.family)
            source = world.oracle_fit if self.probability_mode == "oracle" else world.public_fit
            model.fit(source, universe_size, max_depth)
            self.models[world.slot], self.families[world.slot] = model, world.family
            self.fit_ops += _number(model, "fit_ops")
            if world.family == "program" and self.probability_mode == "oracle":
                self.oracle_roles[world.slot] = tuple(world.oracle_fit.target_by_role)
        self.meta_fit_ops = self.fit_ops

    def query(self, source: PrivilegedQuery, steps: int):
        key = (source.public.slot, source.public.tokens)
        if key in self.memo:
            self.last_ops = self.last_bytes_touched = len(self.memo[key])
            return self.memo[key]
        model, family = self.models[source.public.slot], source.family
        if family == "probabilistic":
            answer = (model.query(source.native, steps),)
        elif family == "predictive":
            history, actions, depth = source.native
            forecast, action = model.query(history, actions, depth)
            answer = (*forecast, action)
        elif family == "local":
            answer = model.query(source.native, steps)
        elif self.probability_mode == "oracle":
            index = source.native.signature % 100
            roles = ((2 + index % 4,) if steps == 1 else
                     (0, 1, 2 + index % 4, 2 + (index * 3) % 4) if steps == 4 else
                     (0, 1, 2 + index % 4, 0, 1, 2 + (index * 3) % 4))
            answer = tuple(self.oracle_roles[source.public.slot][role] for role in roles)
            model.last_ops = 1
        else:
            answer = model.query(source.native, steps)
        self.last_ops = _number(model, "last_ops")
        self.last_bytes_touched = _number(model, "last_bytes_touched", self.last_ops * 8)
        return answer

    def update(self, source: PrivilegedUpdate, target: object) -> None:
        del target
        key = (source.public.query.slot, source.public.query.tokens)
        self.memo[key] = tuple(source.public.target)
        self.update_ops += float(len(source.public.target) + len(source.public.query.tokens))

    def state_bytes(self) -> int:
        return int(sum(_number(model, "state_bytes") for model in self.models.values())
                   + len(self.memo) * 96)


class Candidate(SpecialistSuiteV2):
    pass
