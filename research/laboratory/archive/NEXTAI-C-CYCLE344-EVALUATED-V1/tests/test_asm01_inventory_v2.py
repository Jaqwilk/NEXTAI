"""Synthetic guards for the separately frozen V2 entrypoint; no native payload."""
import ast
import copy
from pathlib import Path

import pytest

from nextai_autoresearch import asm01_grammar_inventory as original
from nextai_autoresearch import asm01_inventory_v2 as entrypoint


def synthetic_checkout(monkeypatch, tmp_path, name="NEXTAI-VALIDATION-20261002"):
    root = tmp_path / name
    root.mkdir()
    monkeypatch.setattr(entrypoint, "__file__", str(root / "src/nextai_autoresearch/asm01_inventory_v2.py"))
    monkeypatch.setattr(entrypoint, "inventory_bytes", lambda *_: pytest.fail("Native payload reached"))
    monkeypatch.setattr(entrypoint, "screen_members", lambda *_: pytest.fail("Native enumeration reached"))
    return root


def test_wrong_checkout_rejected_before_payload(monkeypatch, tmp_path):
    synthetic_checkout(monkeypatch, tmp_path, "OTHER-CHECKOUT")
    with pytest.raises(AssertionError):
        entrypoint.main()


@pytest.mark.parametrize("sentinel", ["STOP", "PAUSE", "research/run.lock"])
def test_stop_rejected_before_payload(monkeypatch, tmp_path, sentinel):
    root = synthetic_checkout(monkeypatch, tmp_path)
    path = root / sentinel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic sentinel", encoding="ascii")
    with pytest.raises(AssertionError):
        entrypoint.main()


def test_wrong_study_hash_rejected_before_payload(monkeypatch, tmp_path):
    root = synthetic_checkout(monkeypatch, tmp_path)
    path = root / entrypoint.STUDY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"synthetic_wrong_plan":true}', encoding="ascii")
    with pytest.raises(AssertionError):
        entrypoint.main()


def test_main_unchanged_except_frozen_bindings_and_hash_metadata():
    assert entrypoint.inventory_bytes is original.inventory_bytes
    assert entrypoint.screen_members is original.screen_members
    assert entrypoint.STUDY == "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.json"
    assert entrypoint.STUDY_SHA == "6351509210dc6ad6f4247665db14ea50aba70e79a6f9dc46b2b0c654e6254726"
    old = ast.parse(Path(original.__file__).read_text(encoding="utf-8"))
    new = ast.parse(Path(entrypoint.__file__).read_text(encoding="utf-8"))
    old_main = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    new_main = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == "main")

    class NormalizeBindings(ast.NodeTransformer):
        def visit_Constant(self, node):
            replacements = {326: 325,
                "ASM01-INVENTORY-V2-PRECONTENT-CONFORMANCE-V1.json": "ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json",
                "research/reviews/ASM01-INVENTORY-V2-PRECONTENT-CONFORMANCE-V1.json": "research/reviews/ASM01-INVENTORY-PRECONTENT-CONFORMANCE-V1.json",
                "ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json": "ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.receipt.json",
                "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V2.receipt.json": "research/reviews/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V1.receipt.json"}
            if node.value in replacements:
                node.value = replacements[node.value]
            return node

        def visit_Dict(self, node):
            self.generic_visit(node)
            fields = []
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "entrypoint_sha256":
                    continue
                if isinstance(key, ast.Constant) and key.value == "scanner_sha256":
                    value = ast.parse("sha256_file(Path(__file__))", mode="eval").body
                fields.append((key, value))
            node.keys = [key for key, _ in fields]
            node.values = [value for _, value in fields]
            return node

    normalized = NormalizeBindings().visit(copy.deepcopy(new_main))
    assert ast.dump(normalized) == ast.dump(old_main)
