#!/usr/bin/env python3
"""Suspended-start Win32 canary containment. Importing never launches anything.

The ONLY process eligible for termination is the child created by this instance,
inside this object's private Job. This is NOT a general service/process manager.
"""
from __future__ import annotations
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

CREATE_SUSPENDED=0x00000004
CREATE_NO_WINDOW=0x08000000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION=9
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE=0x00002000
WAIT_OBJECT_0=0
WAIT_TIMEOUT=0x102
WAIT_FAILED=0xFFFFFFFF
INFINITE=0xFFFFFFFF

class STARTUPINFOW(ctypes.Structure):
    _fields_=[("cb",wintypes.DWORD),("lpReserved",wintypes.LPWSTR),
              ("lpDesktop",wintypes.LPWSTR),("lpTitle",wintypes.LPWSTR),
              ("dwX",wintypes.DWORD),("dwY",wintypes.DWORD),
              ("dwXSize",wintypes.DWORD),("dwYSize",wintypes.DWORD),
              ("dwXCountChars",wintypes.DWORD),("dwYCountChars",wintypes.DWORD),
              ("dwFillAttribute",wintypes.DWORD),("dwFlags",wintypes.DWORD),
              ("wShowWindow",wintypes.WORD),("cbReserved2",wintypes.WORD),
              ("lpReserved2",ctypes.c_void_p),("hStdInput",wintypes.HANDLE),
              ("hStdOutput",wintypes.HANDLE),("hStdError",wintypes.HANDLE)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_=[("hProcess",wintypes.HANDLE),("hThread",wintypes.HANDLE),
              ("dwProcessId",wintypes.DWORD),("dwThreadId",wintypes.DWORD)]

class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_=[("PerProcessUserTimeLimit",ctypes.c_int64),
              ("PerJobUserTimeLimit",ctypes.c_int64),
              ("LimitFlags",wintypes.DWORD),
              ("MinimumWorkingSetSize",ctypes.c_size_t),
              ("MaximumWorkingSetSize",ctypes.c_size_t),
              ("ActiveProcessLimit",wintypes.DWORD),
              ("Affinity",ctypes.c_size_t),
              ("PriorityClass",wintypes.DWORD),
              ("SchedulingClass",wintypes.DWORD)]

class IO_COUNTERS(ctypes.Structure):
    _fields_=[(name,ctypes.c_uint64) for name in
      ("ReadOperationCount","WriteOperationCount","OtherOperationCount",
       "ReadTransferCount","WriteTransferCount","OtherTransferCount")]

class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_=[("BasicLimitInformation",JOBOBJECT_BASIC_LIMIT_INFORMATION),
              ("IoInfo",IO_COUNTERS),
              ("ProcessMemoryLimit",ctypes.c_size_t),
              ("JobMemoryLimit",ctypes.c_size_t),
              ("PeakProcessMemoryUsed",ctypes.c_size_t),
              ("PeakJobMemoryUsed",ctypes.c_size_t)]

def _native_api():
    if sys.platform!="win32" or not hasattr(ctypes,"windll"):
        raise RuntimeError("Windows native process API unavailable")
    api=ctypes.windll.kernel32
    api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
    api.CreateJobObjectW.restype=wintypes.HANDLE
    api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,
                                           ctypes.c_void_p,wintypes.DWORD]
    api.SetInformationJobObject.restype=wintypes.BOOL
    api.CreateProcessW.argtypes=[wintypes.LPCWSTR,wintypes.LPWSTR,
       ctypes.c_void_p,ctypes.c_void_p,wintypes.BOOL,wintypes.DWORD,
       ctypes.c_void_p,wintypes.LPCWSTR,
       ctypes.POINTER(STARTUPINFOW),ctypes.POINTER(PROCESS_INFORMATION)]
    api.CreateProcessW.restype=wintypes.BOOL
    api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
    api.AssignProcessToJobObject.restype=wintypes.BOOL
    api.ResumeThread.argtypes=[wintypes.HANDLE]
    api.ResumeThread.restype=wintypes.DWORD
    api.TerminateProcess.argtypes=[wintypes.HANDLE,wintypes.UINT]
    api.TerminateProcess.restype=wintypes.BOOL
    api.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
    api.TerminateJobObject.restype=wintypes.BOOL
    api.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    api.WaitForSingleObject.restype=wintypes.DWORD
    api.CloseHandle.argtypes=[wintypes.HANDLE]
    api.CloseHandle.restype=wintypes.BOOL
    return api

class ContainedProcess:
    """Creates a process SUSPENDED, assigns it to its own kill-on-close Job,
    then resumes its primary thread. Any failure closes/terminates only its child.
    """
    def __init__(self,api=None):
        self.api=api if api is not None else _native_api()
        self.job=None
        self.info=None
        self.pid=None
        self.contained=False
        self.resumed=False
        self.disposed=False
        self.events=[]

    def start(self,argv,cwd):
        if self.job or self.info or self.disposed:
            raise RuntimeError("contained process instance cannot be reused")
        if not isinstance(argv,(list,tuple)) or len(argv)<2 or not all(
                isinstance(x,str) and x for x in argv):
            raise ValueError("explicit executable and argument strings required")
        if not os.path.isabs(argv[0]) or not os.path.isabs(str(cwd)):
            raise ValueError("absolute interpreter and working directory required")
        try:
            self.job=self.api.CreateJobObjectW(None,None)
            if not self.job:raise OSError("private Job creation failed")
            self.events.append("job_created")
            limits=JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self.api.SetInformationJobObject(self.job,JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                                                     ctypes.byref(limits),ctypes.sizeof(limits)):
                raise OSError("Job kill-on-close guarantee unavailable")
            self.events.append("job_kill_on_close")
            si=STARTUPINFOW();si.cb=ctypes.sizeof(STARTUPINFOW)
            info=PROCESS_INFORMATION()
            command=ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
            flags=CREATE_SUSPENDED | CREATE_NO_WINDOW
            # bInheritHandles=False: none of the parent relay's handles are inherited.
            if not self.api.CreateProcessW(argv[0],command,None,None,False,flags,
                                           None,str(cwd),ctypes.byref(si),ctypes.byref(info)):
                raise OSError("suspended private process creation failed")
            self.info=info
            self.pid=int(info.dwProcessId)
            self.events.append("child_created_suspended")
            if not self.api.AssignProcessToJobObject(self.job,info.hProcess):
                raise OSError("private job assignment failed; child remains suspended")
            self.contained=True
            self.events.append("child_contained")
            if self.api.ResumeThread(info.hThread)==WAIT_FAILED:
                raise OSError("contained child could not resume")
            self.resumed=True
            self.events.append("child_resumed")
            return self
        except BaseException:
            self.close()
            raise

    def poll(self):
        if self.info is None:return None
        wait=self.api.WaitForSingleObject(self.info.hProcess,0)
        if wait==WAIT_TIMEOUT:return None
        if wait==WAIT_OBJECT_0:return 0
        raise OSError("WaitForSingleObject failed for isolated child")

    def close(self):
        if self.disposed:return
        self.disposed=True
        errors=[]
        info=self.info
        job=self.job
        try:
            if info is not None and not self.contained:
                # Failed assignment leaves a suspended child outside the Job.
                if not self.api.TerminateProcess(info.hProcess,1):
                    errors.append("unassigned child termination failed")
                else:
                    self.events.append("unassigned_child_terminated")
            if job:
                if not self.api.TerminateJobObject(job,1):
                    errors.append("private job termination API failed")
                else:
                    self.events.append("private_job_terminated")
            if info is not None:
                wait=self.api.WaitForSingleObject(info.hProcess,3000)
                if wait!=WAIT_OBJECT_0:
                    errors.append("private child exit not observed")
        finally:
            # Always close the private Job handle: kill-on-close is an
            # independent last-resort containment guarantee, even when an
            # earlier native termination call reports an error.
            if info is not None:
                closed_thread=bool(self.api.CloseHandle(info.hThread))
                closed_process=bool(self.api.CloseHandle(info.hProcess))
                if closed_thread and closed_process:
                    self.events.append("child_handles_closed")
                else:
                    errors.append("private child handle close failed")
                self.info=None
            if job:
                if not self.api.CloseHandle(job):
                    errors.append("private job close failed")
                else:
                    self.events.append("job_handle_closed")
                self.job=None
        if errors:raise OSError("; ".join(errors))

    def __enter__(self):return self
    def __exit__(self,*exc):self.close();return False

def containment_contract_self_test():
    from unittest.mock import Mock
    api=Mock()
    api.CreateJobObjectW.return_value=101
    api.SetInformationJobObject.return_value=1
    def create(_exe,_cmd,_pa,_ta,_inherit,flags,_env,_cwd,_si,pi):
        if flags & CREATE_SUSPENDED != CREATE_SUSPENDED:
            raise AssertionError("process not suspended")
        pi._obj.dwProcessId=424242
        pi._obj.hProcess=201
        pi._obj.hThread=202
        return 1
    api.CreateProcessW.side_effect=create
    api.AssignProcessToJobObject.return_value=1
    api.ResumeThread.return_value=1
    api.WaitForSingleObject.return_value=WAIT_OBJECT_0
    instance=ContainedProcess(api)
    # source-independent test fixture, never real OS process
    cmd=[os.path.abspath("not-launched-python.exe"),"-B"]
    instance.start(cmd,os.path.abspath("."))
    instance.close()
    if instance.events[:5]!=[
            "job_created","job_kill_on_close","child_created_suspended",
            "child_contained","child_resumed"]:
        raise RuntimeError("job containment ordering regression")
    return True
