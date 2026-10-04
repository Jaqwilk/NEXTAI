"""Bound ordinary Windows child trees, including descendants of an exited root.

This is trusted auxiliary process control, not the research worker sandbox.
The suspended root joins a kill-on-close job before its first instruction.
Output goes to files, so inherited pipe handles cannot prolong capture.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
import sys
import time

import psutil


class _BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                ("max_working_set", ctypes.c_size_t), ("active_limit", wintypes.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD)]


class _IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("read_count", "write_count", "other_count", "read_bytes", "write_bytes", "other_bytes")]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", _BasicLimits), ("io", _IOCounters),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in
                ("user_time", "kernel_time", "period_user_time", "period_kernel_time")] + [
                (name, wintypes.DWORD) for name in
                ("page_faults", "total_processes", "active_processes", "terminated_processes")]


def _kernel32():
    if sys.platform != "win32":
        raise NotImplementedError("Whole-tree auxiliary supervision requires Windows Job Objects")
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
        "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
        "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        "OpenThread": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        "GetProcessIdOfThread": ([wintypes.HANDLE], wintypes.DWORD),
        "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
        "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
    }
    for name, (args, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = args, result
    return api


def _check(ok):
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())


class _Job:
    def __init__(self):
        self.api, self.handle = _kernel32(), None
        self.handle = self.api.CreateJobObjectW(None, None)
        _check(self.handle)
        try:
            limits = _ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            _check(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        except BaseException:
            self.close()
            raise

    def assign(self, process):
        _check(self.api.AssignProcessToJobObject(self.handle, int(process._handle)))

    def accounting(self):
        result = _Accounting()
        _check(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(result), ctypes.sizeof(result), None))
        return result

    def terminate(self):
        _check(self.api.TerminateJobObject(self.handle, 124))

    def close(self):
        if self.handle is not None:
            handle, self.handle = self.handle, None
            _check(self.api.CloseHandle(handle))


def _resume_initial_process(process, api):
    threads = psutil.Process(process.pid).threads()
    if len(threads) != 1:
        raise RuntimeError("Suspended root does not have exactly one initial thread")
    handle = api.OpenThread(0x0002 | 0x0040, False, threads[0].id)
    _check(handle)
    try:
        if api.GetProcessIdOfThread(handle) != process.pid or api.ResumeThread(handle) != 1:
            raise RuntimeError("Initial thread identity or suspend count is invalid")
    finally:
        _check(api.CloseHandle(handle))


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    root_returncode: int
    reason: str
    elapsed_seconds: float
    pid: int
    processes_created: int
    peak_tree_rss_bytes_sampled: int


def run_bounded(command, *, cwd, env, stdout_path, stderr_path, timeout_seconds):
    """Return after a root exits or the whole job is terminated and drained.

    Timeout includes process construction. Ordinary process creation is a
    synchronous OS call; a stalled OS call cannot be interrupted by Python.
    No descendant is ever resumed outside the owned job. Cleanup is <=3 s.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Timeout must be finite and positive")
    if Path(stdout_path).resolve() == Path(stderr_path).resolve():
        raise ValueError("stdout and stderr must use separate files")
    started = time.monotonic()
    deadline = started + timeout_seconds
    job, process, assigned, cleanup_deadline = _Job(), None, False, None
    peak_rss = 0
    try:
        with Path(stdout_path).open("xb") as stdout, Path(stderr_path).open("xb") as stderr:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, close_fds=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW | 0x00000004)
            job.assign(process)
            assigned = True
            if time.monotonic() < deadline:
                _resume_initial_process(process, job.api)
            while process.poll() is None and time.monotonic() < deadline:
                try:
                    root = psutil.Process(process.pid)
                    rss = 0
                    for item in (root, *root.children(recursive=True)):
                        try:
                            rss += item.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    peak_rss = max(peak_rss, rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                time.sleep(min(.02, max(0., deadline - time.monotonic())))
            accounting = job.accounting()
            reason = ("timeout" if time.monotonic() >= deadline else
                      "lingering_descendants" if accounting.active_processes else "exited")
            cleanup_deadline = time.monotonic() + 3.
            if reason != "exited":
                job.terminate()
            while job.accounting().active_processes and time.monotonic() < cleanup_deadline:
                time.sleep(.01)
            if job.accounting().active_processes:
                raise RuntimeError("Job did not drain within bounded cleanup")
            root_code = process.wait(timeout=max(.01, cleanup_deadline - time.monotonic()))
            return ProcessResult(root_code if reason == "exited" else 124, root_code, reason,
                                 time.monotonic() - started, process.pid, accounting.total_processes, peak_rss)
    finally:
        # Closing the sole non-inherited handle also kills orphaned descendants.
        try:
            job.close()
        finally:
            if process is not None and process.poll() is None:
                if not assigned:
                    process.kill()  # Still suspended; assignment failed before execution.
                remaining = 3. if cleanup_deadline is None else max(.001, cleanup_deadline - time.monotonic())
                process.wait(timeout=remaining)
