"""Trusted prospective cumulative CUDA allocator peaks, outside service timing."""
import psutil

VERSION = "cumulative_cuda_phase_peaks_v1"
PHASES = ("initializing", "fit", "evaluation", "complete")


def take_peak_snapshot(phase, torch, limits):
    if phase not in PHASES:
        raise ValueError("Unknown resource snapshot phase")
    cuda = torch.cuda
    available = bool(cuda.is_available())
    if available:
        cuda.synchronize()
    sample = {"phase": phase, "cuda_available": available,
              "cuda_peak_allocated_bytes": int(cuda.max_memory_allocated()) if available else 0,
              "cuda_peak_reserved_bytes": int(cuda.max_memory_reserved()) if available else 0,
              "process_rss_bytes": int(psutil.Process().memory_info().rss)}
    _validate_sample(sample, limits)
    return sample


def _validate_sample(sample, limits):
    if sample.get("phase") not in PHASES or type(sample.get("cuda_available")) is not bool:
        raise ValueError("Invalid trusted resource snapshot identity")
    values = [sample.get(k) for k in ("cuda_peak_allocated_bytes", "cuda_peak_reserved_bytes", "process_rss_bytes")]
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("Invalid trusted resource byte count")
    allocated, reserved, rss = values
    if allocated > reserved or reserved > limits["max_cuda_reserved_bytes"] or rss == 0:
        raise ValueError("Trusted resource evidence exceeds frozen cap or is inconsistent")
    if not sample["cuda_available"] and (allocated or reserved):
        raise ValueError("Unavailable CUDA cannot report nonzero allocator bytes")


def validate_peak_record(record, limits, *, require_complete=True):
    if not isinstance(record, dict) or record.get("schema_version") != 1 or record.get("version") != VERSION or record.get("timed_service_modified") is not False:
        raise ValueError("Trusted resource schema/boundary mismatch")
    rows = record.get("snapshots")
    if not isinstance(rows, list) or not rows or len(rows) > len(PHASES) or any(not isinstance(r, dict) for r in rows):
        raise ValueError("Missing or excessive trusted resource snapshots")
    if tuple(r.get("phase") for r in rows) != PHASES[:len(rows)] or require_complete and len(rows) != len(PHASES):
        raise ValueError("Missing,duplicate or out-of-order trusted resource phase")
    for row in rows:
        _validate_sample(row, limits)
    for key in ("cuda_peak_allocated_bytes", "cuda_peak_reserved_bytes"):
        if any(b[key] < a[key] for a,b in zip(rows,rows[1:])):
            raise ValueError("Cumulative CUDA peak decreased")
    if len({r["cuda_available"] for r in rows}) != 1:
        raise ValueError("CUDA availability changed within worker")
    return True
