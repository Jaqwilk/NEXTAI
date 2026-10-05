from pathlib import Path
import json
b=Path.cwd()
s=(b/'src/nextai_autoresearch/pvm01_task.py').read_text()
views=s[s.index('def views('):s.index('\n\ndef pairs(')].replace('values, rng):','values, rng, noise):').replace('normal(0, .02,','normal(0, noise,')
episode=s[s.index('def episode('):s.index('\n\ndef training_sets(')]
episode=episode.replace('query_count=64):','query_count=64, *, noise=.02):\n    if noise not in (.02, .04):\n        raise ValueError("Only preregistered observation noise conditions")')
episode=episode.replace('values, rng)','values, rng, noise)').replace('values[i:i + 1], rng)','values[i:i + 1], rng, noise)').replace('query_values, rng)','query_values, rng, noise)')
p=b/'src/nextai_autoresearch/pvm01_adverse_task.py';assert not p.exists();p.write_text('"""New adverse cohort: same latent/truth draws, fixed noise magnitude interaction."""\nimport numpy as np\nfrom .pvm01_task import Episode, rng_for, maps, identities\n\n\n'+views+'\n\n\n'+episode+'\n',encoding='utf-8',newline='\n')
p=b/'src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v6.py';assert not p.exists()
old=(b/'src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v5.py').read_text();head=old[:old.index('\ndef exposure_training_sets')];body=old[old.index('\ndef run_suite'):]
head=head.replace('Prospective capacity exposure; unchanged task law, scoring and measurement.','Prospective transport compression and paired adverse noise; unchanged scoring/costs.').replace('paired_view_mutable_memory_v5','paired_view_mutable_memory_v6').replace('from ..pvm01_task import','from torch.nn.attention import SDPBackend, sdpa_kernel\nfrom ..pvm01_adverse_task import episode as adverse_episode\nfrom ..pvm01_task import')
body=body.replace('compact = arm.startswith("exposure_") or arm == "delta"','compact = arm == "delta"').replace('sets = exposure_training_sets(nonce)','sets = training_sets(nonce)')
oldfit='    report = system.fit(writes, queries, held_writes, held_queries, sets)'
newfit='''    deterministic = torch.are_deterministic_algorithms_enabled()
    warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.use_deterministic_algorithms(True)
        with sdpa_kernel(SDPBackend.MATH):
            policy = {"deterministic": torch.are_deterministic_algorithms_enabled(),
                      "warn_only": torch.is_deterministic_algorithms_warn_only_enabled(),
                      "math_sdp": torch.backends.cuda.math_sdp_enabled(),
                      "efficient_sdp": torch.backends.cuda.mem_efficient_sdp_enabled(),
                      "flash_sdp": torch.backends.cuda.flash_sdp_enabled(),
                      "cudnn_sdp": torch.backends.cuda.cudnn_sdp_enabled()}
            report = system.fit(writes, queries, held_writes, held_queries, sets)
            report["fit_policy_snapshot"] = policy
    finally:
        torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)'''
assert body.count(oldfit)==1;body=body.replace(oldfit,newfit)
start=body.index('    for size in matrix["knowledge_sizes"]:',body.index('    trials = []'))
end=body.index('    if phase_sink:\n        phase_sink("complete")',start)
block=body[start:end]
block=block.replace('worlds = [episode(nonce, "D", size, rounds, i)','worlds = [adverse_episode(nonce, "D", size, rounds, i, noise=observation_noise)')
block=block.replace('"split": "D",','"split": "D", "observation_noise": observation_noise,')
block=block.replace('"status": "complete", "seed": seed,','"status": "complete", "observation_noise": observation_noise, "seed": seed,')
block=block.replace('"data_generation_seconds": generation, "full_workload_seconds":','"truth_pair_sha256": sha256_json([[w.answers, w.target_handles, w.strata, [(r[0], r[1], r[3]) for r in w.writes]] for w in worlds]),\n                     "data_generation_seconds": generation, "full_workload_seconds":')
body=body[:start]+'    for observation_noise in protocol["data"]["evaluation_noise_standard_deviations"]:\n'+''.join('    '+line if line.strip() else line for line in block.splitlines(keepends=True))+body[end:]
p.write_text(head+body,encoding='utf-8',newline='\n')
spec=json.loads((b/'research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json').read_text())
for name,role in spec['roles'].items():
 a=role['arm']; core='pvm01_transport_compression_core' if a.startswith('transport_') else 'pvm01_repro_core' if a.startswith('dense') else 'pvm01_optimized_core' if a in ('ridge32','ridge_pca_scan','ridge_pca_tree') else 'pvm01_delta_core' if a=='delta' else 'pvm01_core'
 p=b/f'src/nextai_autoresearch/candidates/{name}.py';assert not p.exists();p.write_text(f'"""Frozen v6 role; shared audited implementation."""\nfrom .{core} import Candidate\n',encoding='utf-8',newline='\n')
for name in ['src/nextai_autoresearch/runner.py','src/nextai_autoresearch/research_program.py','schemas/experiment_plan.schema.json']:
 p=b/name; raw=p.read_bytes(); old=b'"paired_view_mutable_memory_v5"'; assert old in raw; p.write_bytes(raw.replace(old,old+b', "paired_view_mutable_memory_v6"'))
p=b/'src/nextai_autoresearch/research_program.py';raw=p.read_text(); anchor='    for identity, relative in previous.items():'
assert raw.count(anchor)==1;raw=raw.replace(anchor,'    previous["EXP-20261004-0008"] = "research/laboratory/archive/EXP-20261004-0008-runtime/research/tmp/EXP-20261004-0008"\n'+anchor);p.write_text(raw,encoding='utf-8',newline='\n')
print('New evaluator/task/core/70 aliases and exact dispatch extension written; no data or fit')
registry=json.loads((b/'config/baseline_semantics.json').read_text());print('v5cohort',next(c for c in registry['cohorts'] if c.get('benchmark_version')=='paired_view_mutable_memory_v5'))
