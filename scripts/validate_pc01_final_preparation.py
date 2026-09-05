"""Read-only proof of the no-training final-series preparation."""
import json
from nextai_autoresearch.utils import project_root, load_json, sha256_file
from nextai_autoresearch.pc01_final_transition import selected_transition, PLAN_PATH
from nextai_autoresearch.pc01_execution import SERIES
from nextai_autoresearch.laboratory import final_preparation_status
from validate_pc01_gpu_metadata import main as previous_proof


def main():
    root = project_root()
    previous_proof()
    policy = load_json(root / PLAN_PATH)
    assert final_preparation_status(root) is not None
    assert not (root / SERIES).exists()
    manifest = root / policy["archive_manifest"]
    assert sha256_file(manifest) == "a802d2a7b1b3727f15e8f743dc27e12c44299651e30ebc6a590fdba3ebb13fb1"
    old = load_json(manifest)
    for relative, digest in old["files"].items():
        assert sha256_file(root / policy["archive"] / relative) == digest, relative
    transition = selected_transition(root, policy["selected_dev_id"])
    print(json.dumps(dict(archived_protected_files=len(old["files"]), transition=transition,
                         training_performed=False, final_access_authorized=False)))


if __name__ == "__main__":
    main()
