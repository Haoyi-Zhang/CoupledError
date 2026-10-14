"""Honest resource support for owned finite tests; no dependency installation.

Linux keeps the existing CPU/address-space limits. Windows is an explicitly
requested portable run: real affinity and working-set measurements, no claimed
POSIX limits or child CPU accounting. Never imported by certificate replay.
"""
import os
import sys

try:
    import resource
except ImportError:
    resource = None


def configure():
    if resource is not None:
        if hasattr(os, "sched_getaffinity"):
            os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
        resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
        return
    if os.name != "nt" or os.environ.get("COUPLEDERROR_PORTABLE") != "1":
        raise RuntimeError("Linux resource envelope unavailable; explicitly set COUPLEDERROR_PORTABLE=1 for uncapped Windows tests")
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    process, system = ctypes.c_size_t(), ctypes.c_size_t()
    handle = kernel.GetCurrentProcess()
    if not kernel.GetProcessAffinityMask(handle, ctypes.byref(process), ctypes.byref(system)):
        raise ctypes.WinError(ctypes.get_last_error())
    mask = process.value & -process.value
    if not mask or not kernel.SetProcessAffinityMask(handle, mask):
        raise ctypes.WinError(ctypes.get_last_error())


def peak_rss_kib():
    if resource is not None:
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value / 1024 if sys.platform == "darwin" else value
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    api = ctypes.WinDLL("psapi", use_last_error=True)
    api.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not api.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.PeakWorkingSetSize / 1024


def capabilities():
    return {"platform": sys.platform, "portable_requested": os.environ.get("COUPLEDERROR_PORTABLE") == "1",
            "posix_cpu_and_address_limits": resource is not None,
            "memory_measurement": "ru_maxrss" if resource is not None else "Windows PeakWorkingSetSize",
            "child_cpu_accounting": resource is not None}
