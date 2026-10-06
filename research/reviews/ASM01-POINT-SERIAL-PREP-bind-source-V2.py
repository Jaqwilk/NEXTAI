"""Bind stronger named fixtures BEFORE the first test; preserve V1 binding."""
from pathlib import Path
from nextai_autoresearch.utils import atomic_write_json, load_json, sha256_file, utc_now
root = Path.cwd()
old_path = root / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V1.json'
binding = load_json(old_path)
assert not (root / 'research/reviews/ASM01-POINT-SERIAL-PREP-CONTROLLER-V1.started.json').exists()
assert binding['source_sha256'] == sha256_file(root / binding['source_path'])
path = root / 'research/reviews/ASM01-POINT-SERIAL-PREP-SOURCE-BINDINGS-V2.json'
assert not path.exists()
binding.update(created_at=utc_now(), fixture_sha256=sha256_file(root / binding['fixture_path']),
 prior_binding_sha256=sha256_file(old_path), prior_fixture_sha256=binding['fixture_sha256'],
 change_before_any_test=True, prior_test_executions=0,
 refinement='Same frozen38 named cases: oversize-normalized now checks both full exact-length16384 and early count20000; history invariant checks all3 ledger prefixes and parent-binding SHA. No plan, normalizer, model, native or threshold changes.')
atomic_write_json(path, binding)
print(binding)
