#!/usr/bin/env python3
"""Evidence-backed ownership of the HTTP host in a PRIVATE Win32 Job.

A venv python.exe on Windows can be a redirector that creates another Python
process. Do not equate an authenticated status PID with the launcher PID, but
never permit arbitrary PIDs: verify the listening process is in the *exact*
owned Job and is the launcher or its direct child. Hold a real process handle
until Job termination so PID recycling cannot fake exit verification.
This module does not launch, terminate, or enumerate processes.
"""
from __future__ import annotations
import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

PROCESS_QUERY_LIMITED_INFORMATION=0x1000
SYNCHRONIZE=0x00100000
WAIT_OBJECT_0=0

class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_=[("Reserved1",ctypes.c_void_p),
              ("PebBaseAddress",ctypes.c_void_p),
              ("Reserved2",ctypes.c_void_p*2),
              ("UniqueProcessId",ctypes.c_size_t),
              ("InheritedFromUniqueProcessId",ctypes.c_size_t)]

def _native_api():
    if sys.platform!="win32":
        raise RuntimeError("private host identity requires Win32")
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    n=ctypes.WinDLL("ntdll",use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.OpenProcess.restype=wintypes.HANDLE
    k.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]
    k.IsProcessInJob.restype=wintypes.BOOL
    k.GetProcessId.argtypes=[wintypes.HANDLE]
    k.GetProcessId.restype=wintypes.DWORD
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,
                                            ctypes.POINTER(wintypes.DWORD)]
    k.QueryFullProcessImageNameW.restype=wintypes.BOOL
    k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    k.WaitForSingleObject.restype=wintypes.DWORD
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    k.CloseHandle.restype=wintypes.BOOL
    n.NtQueryInformationProcess.argtypes=[wintypes.HANDLE,wintypes.ULONG,ctypes.c_void_p,
                   wintypes.ULONG,ctypes.POINTER(wintypes.ULONG)]
    n.NtQueryInformationProcess.restype=ctypes.c_long
    return k,n

class PrivateHost:
    """One held query/wait-only handle to an independently attested private host."""
    def __init__(self,pid,launcher_pid,job,kernel=None,ntdll=None):
        if type(pid) is not int or pid<=0 or type(launcher_pid) is not int or launcher_pid<=0:
            raise RuntimeError("non-integer private host/launcher identity")
        if not job:
            raise RuntimeError("private Job handle missing")
        if kernel is None or ntdll is None:
            kernel,ntdll=_native_api()
        self.kernel=kernel
        self.handle=None
        self.pid=pid
        self.launcher_pid=launcher_pid
        self.job_member=False
        self.parent_pid=None
        self.host_image=None
        self.verified=False
        self.exit_observed=False
        try:
            handle=kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,False,pid)
            if not handle:raise OSError("private HTTP host cannot be opened for query/wait")
            self.handle=handle
            if kernel.GetProcessId(handle)!=pid:
                raise RuntimeError("opened process identity changed")
            attached=wintypes.BOOL()
            if not kernel.IsProcessInJob(handle,job,ctypes.byref(attached)):
                raise OSError("exact private Job membership query failed")
            self.job_member=bool(attached.value)
            if not self.job_member:
                raise RuntimeError("HTTP host not in the exact private Job")
            info=PROCESS_BASIC_INFORMATION()
            written=wintypes.ULONG()
            if ntdll.NtQueryInformationProcess(handle,0,ctypes.byref(info),
                                                 ctypes.sizeof(info),ctypes.byref(written))!=0:
                raise OSError("HTTP host ancestry query failed")
            if int(info.UniqueProcessId)!=pid:
                raise RuntimeError("ancestry queried a different PID")
            self.parent_pid=int(info.InheritedFromUniqueProcessId)
            if pid!=launcher_pid and self.parent_pid!=launcher_pid:
                raise RuntimeError("HTTP host is not the contained launcher's direct child")
            # Image identity augments private Job membership and ancestry.
            buffer=ctypes.create_unicode_buffer(32768)
            size=wintypes.DWORD(len(buffer))
            if not kernel.QueryFullProcessImageNameW(handle,0,buffer,ctypes.byref(size)):
                raise OSError("HTTP host executable identity query failed")
            self.host_image=str(buffer.value[:size.value])
            if Path(self.host_image).name.lower() not in ("python.exe","pythonw.exe"):
                raise RuntimeError("private HTTP host executable is not Python")
            self.verified=True
        except BaseException:
            self.close()
            raise

    def wait_for_exit(self,ms=4000):
        if not self.handle or not self.verified:
            raise RuntimeError("unverified host cannot establish termination")
        self.exit_observed=self.kernel.WaitForSingleObject(self.handle,ms)==WAIT_OBJECT_0
        if not self.exit_observed:
            raise RuntimeError("private HTTP host did not exit after Job termination")
        return True

    def close(self):
        if self.handle:
            handle=self.handle
            self.handle=None
            if not self.kernel.CloseHandle(handle):
                raise OSError("private HTTP host query handle close failed")

def attest_private_host(pid,launcher_pid,job):
    """Return a held ownership proof, caller MUST wait_for_exit then close."""
    return PrivateHost(pid,launcher_pid,job)
