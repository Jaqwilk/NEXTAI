from pathlib import Path
import json, subprocess
from nextai_autoresearch.utils import sha256_file

b=Path.cwd(); prereg=json.loads((b/'research/tmp/PVM01-CONFIRMATION-preregistration-V1.json').read_text(encoding='utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==prereg['preregistration_git_commit']
study=json.loads((b/prereg['study_path']).read_text(encoding='utf-8'))
addon_rel='research/plans/PVM01-CONFIRMATION-CLASSICAL-ECONOMICS-V1.json'; addon_hash=sha256_file(b/addon_rel)
def edit(rel, changes):
    p=b/rel; text=p.read_text(encoding='utf-8')
    for old,new,count in changes:
        assert text.count(old)==count,(rel,old,text.count(old)); text=text.replace(old,new)
    p.write_text(text,encoding='utf-8',newline='\n')
edit('src/nextai_autoresearch/research_program.py',[
    ('    return {**extra, **{key: study[key] for key in',f'''    if study.get("study_kind") == "paired_view_dense_noise_confirmation":
        extra.update(classical_economic_contract_path="{addon_rel}",
                     classical_economic_contract_sha256="{addon_hash}",
                     resource_measurement_version="cumulative_cuda_phase_peaks_v1")
    return {{**extra, **{{key: study[key] for key in''',1),
    ('include_replication=False):','include_replication=False, include_dense_noise=False):',1),
    ('    for identity, relative in previous.items():','''    if include_dense_noise:
        if not include_latest or not include_transport or not include_replication:
            raise ValueError("Dense-noise confirmation requires all earlier PVM histories")
        previous["EXP-20261005-0003"] = "research/laboratory/archive/EXP-20261005-0003-runtime/research/tmp/EXP-20261005-0003"
    for identity, relative in previous.items():''',1),
    ('"paired_view_mutable_memory_v8")','"paired_view_mutable_memory_v8", "paired_view_mutable_memory_v9")',1)])
edit('src/nextai_autoresearch/runner.py',[
    ('"paired_view_mutable_memory_v8")','"paired_view_mutable_memory_v8", "paired_view_mutable_memory_v9")',1),
    ('"paired_view_mutable_memory_v8"}','"paired_view_mutable_memory_v8", "paired_view_mutable_memory_v9"}',2),
    ('                    if plan["benchmark"] == "paired_view_mutable_memory_v8":','''                    if plan["benchmark"] == "paired_view_mutable_memory_v9":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True, include_transport=True, include_replication=True, include_dense_noise=True)
                    elif plan["benchmark"] == "paired_view_mutable_memory_v8":''',1),
    ('    return {\n        "candidate": candidate,\n        "status": worker_output.get("status", "crash"),','''    if limits.get("resource_measurement_version") == "cumulative_cuda_phase_peaks_v1":
        from .worker_resource_peaks import validate_peak_record
        resource_path = output_path.with_suffix(".resources.json")
        try:
            record = load_json(resource_path)
            validate_peak_record(record, limits, require_complete=worker_output.get("status") == "complete")
            execution["resource_peaks"] = record
            execution["resource_peaks_path"] = relative_posix(resource_path, root)
            execution["resource_peaks_sha256"] = sha256_file(resource_path)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            execution["resource_peaks_error"] = str(exc)
            if worker_output.get("status") == "complete":
                worker_output["status"] = "telemetry_failure"
                worker_output["error"] = "Missing or invalid trusted final CUDA/RSS evidence"
    return {
        "candidate": candidate,
        "status": worker_output.get("status", "crash"),''',1)])
edit('src/nextai_autoresearch/worker_resources.py',[
    ('        self.torch = None','        self.torch = None\n        self.resource_snapshots = []',1),
    ('        now = time.monotonic()\n        if name == "fit":','''        if self.limits.get("resource_measurement_version") == "cumulative_cuda_phase_peaks_v1":
            from .worker_resource_peaks import take_peak_snapshot
            self.resource_snapshots.append(take_peak_snapshot(name, self.torch, self.limits))
            atomic_write_json(self.output.with_suffix(".resources.json"), {
                "schema_version": 1, "version": "cumulative_cuda_phase_peaks_v1",
                "snapshots": self.resource_snapshots,
                "gpu_boundary": "Cumulative PyTorch allocator/reservation peaks since worker start; driver/context VRAM and energy unmeasured",
                "cpu_boundary": "Root-worker RSS snapshots; parent sampled process-tree peak reported separately",
                "timed_service_modified": False})
        now = time.monotonic()
        if name == "fit":''',1)])
edit('src/nextai_autoresearch/integrity.py',[
    ('FIXED_PROTECTED_FILES = (','FIXED_PROTECTED_FILES = (\n    "scripts/analyze_pvm01_confirmation.py",\n    "scripts/run_pvm01_confirmation_check.py",',1)])
wrapper=(b/'scripts/run_pvm01_dense_noise_check.py').read_text(encoding='utf-8').replace('cycle314 dense-noise contract','cycle315 independent confirmation contract').replace('PVM01-DENSE-NOISE-ROBUSTNESS-V1.json','PVM01-DENSE-NOISE-CONFIRMATION-V1.json').replace('PVM01-ROBUSTNESS-','PVM01-CONFIRMATION-').replace('.read_text()',".read_text(encoding='utf-8')")
(b/'scripts/run_pvm01_confirmation_check.py').write_text(wrapper,encoding='utf-8',newline='\n')
p=b/'schemas/experiment_plan.schema.json'; schema=json.loads(p.read_text(encoding='utf-8')); props=schema['properties']['research_program_protocol']['properties']
props['classical_economic_contract_path']['enum'].append(addon_rel); props['classical_economic_contract_sha256']['enum'].append(addon_hash)
props['resource_measurement_version']={'const':'cumulative_cuda_phase_peaks_v1'}
for i in (64,65): schema['allOf'][i]['if']['properties']['benchmark']['enum'].append('paired_view_mutable_memory_v9')
schema['allOf'].append({'if':{'properties':{'benchmark':{'const':'paired_view_mutable_memory_v9'}},'required':['benchmark']},
    'then':{'properties':{'research_program_protocol':{'required':['resource_measurement_version'],'properties':{'classical_economic_contract_path':{'const':addon_rel},'classical_economic_contract_sha256':{'const':addon_hash},'resource_measurement_version':{'const':'cumulative_cuda_phase_peaks_v1'}}}}},
    'else':{'properties':{'research_program_protocol':{'properties':{'resource_measurement_version':False}}}}})
p.write_text(json.dumps(schema,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
for rel,digest in study['parent_evidence']['scientific_source_sha256_unchanged'].items(): assert sha256_file(b/rel)==digest,rel
print('Audited v9 integration and trusted phase evidence; all selected scientific recipes/source bytes unchanged',flush=True)
