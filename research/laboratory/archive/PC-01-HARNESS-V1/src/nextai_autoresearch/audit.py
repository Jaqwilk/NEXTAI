from __future__ import annotations

import ast
import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path

from .config import ResearchConfig
from .utils import project_root, sha256_file


CANDIDATE_NAME = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
FORBIDDEN_INTERNAL_PREFIXES = (
    "nextai_autoresearch.pc01",
    "nextai_autoresearch.benchmarks",
    "nextai_autoresearch.cli",
    "nextai_autoresearch.doctor",
    "nextai_autoresearch.gates",
    "nextai_autoresearch.integrity",
    "nextai_autoresearch.ledger",
    "nextai_autoresearch.report",
    "nextai_autoresearch.runner",
    "nextai_autoresearch.schemas",
    "nextai_autoresearch.worker",
)

RELATIONAL_PRIVATE_IDENTIFIERS = frozenset(
    {
        "z",
        "q",
        "latent",
        "latent_records",
        "stable_latent",
        "nuisance_latent",
        "probe_latent",
        "source_id",
        "source_ids",
        "nuisance",
        "oracle",
        "role",
        "first_basis",
        "second_basis",
        "probe_basis",
        "m_s",
        "m_n",
        "world_identity",
        "twin_world",
        "matching_type",
        "coordinate_permutation",
        "inverse_permutation",
        "inverse_mixer",
    }
)
RELATIONAL_ROLE_LITERALS = frozenset(
    {
        "correct",
        "shuffled",
        "passive",
        "random",
        "classical",
        "oracle",
        "w_swap",
        "m_s",
        "m_n",
        "orthogonal_double_matching_source_swap_v1",
    }
)


@dataclass(frozen=True)
class AuditResult:
    ok: bool
    candidate: str
    path: Path
    sha256: str | None
    problems: tuple[str, ...]
    dependencies: tuple[tuple[Path, str], ...] = ()


def audit_relational_candidate_source(source: str) -> tuple[str, ...]:
    """Enforce the anonymous relational evaluator's candidate boundary.

    The check is separate from the legacy candidate audit so historical
    candidates remain inspectable.  An activated relational evaluator must run
    this check before accepting a candidate; the v1 evaluator currently stays
    in maintenance and independently hard-stops every scoring attempt.
    """

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return (f"candidate source does not parse: {exc}",)
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id.lower() in RELATIONAL_PRIVATE_IDENTIFIERS:
            problems.append(
                f"line {node.lineno}: evaluator-private identifier {node.id!r} is forbidden"
            )
        elif isinstance(node, ast.Attribute):
            attribute = node.attr.lower()
            if attribute in RELATIONAL_PRIVATE_IDENTIFIERS:
                problems.append(
                    f"line {node.lineno}: evaluator-private attribute {node.attr!r} is forbidden"
                )
            if attribute == "random":
                problems.append(
                    f"line {node.lineno}: candidate-owned randomness is forbidden by the frozen contract"
                )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            literal = node.value.strip().lower()
            if literal in RELATIONAL_ROLE_LITERALS:
                problems.append(
                    f"line {node.lineno}: role-specific literal {node.value!r} is forbidden"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] in {"random", "secrets"}:
                    problems.append(
                        f"line {node.lineno}: candidate-owned randomness import {alias.name!r} is forbidden"
                    )
                if alias.name.startswith("nextai_autoresearch.benchmarks"):
                    problems.append(
                        f"line {node.lineno}: importing a protected evaluator {alias.name!r} is forbidden"
                    )
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".", 1)[0] in {"random", "secrets"}:
                problems.append(
                    f"line {node.lineno}: candidate-owned randomness import {node.module!r} is forbidden"
                )
            if (node.module or "").startswith("nextai_autoresearch.benchmarks"):
                problems.append(
                    f"line {node.lineno}: importing a protected evaluator {node.module!r} is forbidden"
                )
    return tuple(dict.fromkeys(problems))


def candidate_path(candidate: str, root: Path | None = None) -> Path:
    if not CANDIDATE_NAME.fullmatch(candidate):
        raise ValueError(f"Invalid candidate name: {candidate!r}")
    return (
        (root or project_root())
        / "src"
        / "nextai_autoresearch"
        / "candidates"
        / f"{candidate}.py"
    )


def _module_name(path: Path, package_root: Path) -> str:
    relative = path.resolve().relative_to(package_root.parent.resolve())
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _local_module_path(module: str, package_root: Path) -> Path | None:
    if module == "nextai_autoresearch":
        candidate = package_root / "__init__.py"
        return candidate if candidate.is_file() else None
    prefix = "nextai_autoresearch."
    if not module.startswith(prefix):
        return None
    relative = Path(*module[len(prefix) :].split("."))
    module_path = package_root / relative.with_suffix(".py")
    if module_path.is_file():
        return module_path
    package_path = package_root / relative / "__init__.py"
    return package_path if package_path.is_file() else None


def _resolved_imports(
    node: ast.Import | ast.ImportFrom,
    current_module: str,
    package_root: Path,
) -> list[tuple[str, Path]]:
    modules: list[str] = []
    if isinstance(node, ast.Import):
        modules.extend(alias.name for alias in node.names)
    else:
        module = node.module or ""
        if node.level:
            package = current_module.rpartition(".")[0]
            try:
                module = importlib.util.resolve_name(
                    "." * node.level + module, package
                )
            except (ImportError, ValueError):
                module = ""
        if module:
            modules.append(module)
            modules.extend(f"{module}.{alias.name}" for alias in node.names)
    resolved: list[tuple[str, Path]] = []
    for module in modules:
        path = _local_module_path(module, package_root)
        if path is not None:
            resolved.append((module, path))
    return resolved


def audit_candidate(
    candidate: str, config: ResearchConfig, root: Path | None = None
) -> AuditResult:
    base = (root or project_root()).resolve()
    path = candidate_path(candidate, base)
    if not path.is_file():
        return AuditResult(False, candidate, path, None, ("candidate source is missing",))

    package_root = base / "src" / "nextai_autoresearch"
    problems: list[str] = []
    dependencies: dict[Path, str] = {}
    pending = [path]
    visited: set[Path] = set()
    entry_tree: ast.Module | None = None

    while pending:
        current = pending.pop().resolve()
        if current in visited:
            continue
        visited.add(current)
        try:
            source = current.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(current))
        except (OSError, SyntaxError, UnicodeError) as exc:
            problems.append(f"{current.name}: {exc}")
            continue
        if current == path.resolve():
            entry_tree = tree
        dependencies[current] = sha256_file(current)
        current_module = _module_name(current, package_root)
        display = current.relative_to(base).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = (
                    ["nextai_autoresearch"] if node.level else [node.module or ""]
                )
            else:
                imported = []
            for module in imported:
                root_name = module.split(".", 1)[0]
                if root_name and root_name not in config.allowed_import_roots:
                    problems.append(
                        f"{display}:{node.lineno}: forbidden import {module!r}"
                    )
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for module, dependency in _resolved_imports(
                    node, current_module, package_root
                ):
                    if module.startswith(FORBIDDEN_INTERNAL_PREFIXES):
                        problems.append(
                            f"{display}:{node.lineno}: candidate dependency crosses evaluator boundary into {module!r}"
                        )
                    else:
                        pending.append(dependency)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in config.forbidden_builtins:
                    problems.append(
                        f"{display}:{node.lineno}: forbidden builtin {node.func.id!r}"
                    )

    if entry_tree is not None:
        exported = [
            node
            for node in entry_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Candidate"
        ]
        if len(exported) != 1:
            problems.append("candidate module must export exactly one class named Candidate")
    unique_problems = tuple(dict.fromkeys(problems))
    ordered_dependencies = tuple(
        sorted(dependencies.items(), key=lambda item: item[0].as_posix())
    )
    return AuditResult(
        ok=not unique_problems,
        candidate=candidate,
        path=path,
        sha256=dependencies.get(path.resolve()),
        problems=unique_problems,
        dependencies=ordered_dependencies,
    )


def audit_benchmark_boundary(
    benchmark: str, root: Path | None = None
) -> tuple[str, ...]:
    """Reject active evaluator imports of candidate implementation modules."""
    base = (root or project_root()).resolve()
    path = base / "src" / "nextai_autoresearch" / "benchmarks" / f"{benchmark}.py"
    if not path.is_file():
        return (f"benchmark source is missing: {path}",)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        return (str(exc),)
    problems: list[str] = []
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        for module in modules:
            normalized = module.replace("/", ".")
            if normalized.endswith("_core") or ".candidates" in normalized:
                problems.append(
                    f"line {node.lineno}: evaluator imports candidate implementation module {module!r}; move shared types to a *_contract module"
                )
    return tuple(problems)
