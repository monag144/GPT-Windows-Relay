"""Static and injected API verification for suspended private Win32 canary jobs."""
from __future__ import annotations
import importlib.util
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock

FILE=Path(__file__).resolve().parents[1]/"tools"/"pce11_win32_containment.py"
spec=importlib.util.spec_from_file_location("pce11_win32_containment",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ContainmentContractTests(unittest.TestCase):
    def fake_api(self, failure=None):
        api=Mock()
        api.CreateJobObjectW.return_value=111
        api.SetInformationJobObject.return_value=1
        api.AssignProcessToJobObject.return_value=0 if failure=="assign" else 1
        api.ResumeThread.return_value=mod.WAIT_FAILED if failure=="resume" else 1
        api.WaitForSingleObject.return_value=mod.WAIT_OBJECT_0
        def create(_app,cmd,_p,_t,inherit,flags,_env,_cwd,_si,out):
            self.assertFalse(inherit)
            self.assertEqual(flags & mod.CREATE_SUSPENDED,mod.CREATE_SUSPENDED)
            self.assertEqual(flags & mod.CREATE_NO_WINDOW,mod.CREATE_NO_WINDOW)
            self.assertIn("-B",cmd.value)
            out._obj.hProcess=222
            out._obj.hThread=333
            out._obj.dwProcessId=4444
            out._obj.dwThreadId=5555
            return 1
        api.CreateProcessW.side_effect=create
        if failure=="create":api.CreateProcessW.return_value=0;api.CreateProcessW.side_effect=None
        if failure=="job":api.SetInformationJobObject.return_value=0
        return api

    def arguments(self):
        return [os.path.abspath("dummy-do-not-launch.exe"),"-B"],os.path.abspath(".")

    def test_contract_selftest(self):
        self.assertTrue(mod.containment_contract_self_test())

    def test_success_is_suspended_then_assigned_then_resumed(self):
        a=self.fake_api()
        args,cwd=self.arguments()
        p=mod.ContainedProcess(a)
        p.start(args,cwd)
        self.assertEqual(p.pid,4444)
        self.assertTrue(p.contained)
        self.assertTrue(p.resumed)
        self.assertEqual(p.events[:5],[
          "job_created","job_kill_on_close","child_created_suspended",
          "child_contained","child_resumed"])
        self.assertEqual(p.poll(),0)
        p.close()
        self.assertTrue(p.disposed)
        a.TerminateProcess.assert_not_called()
        a.TerminateJobObject.assert_called_once()
        self.assertEqual(a.CloseHandle.call_count,3)

    def test_failed_job_assignment_terminates_suspended_child(self):
        a=self.fake_api("assign")
        args,cwd=self.arguments()
        with self.assertRaisesRegex(OSError,"private job assignment"):
            mod.ContainedProcess(a).start(args,cwd)
        a.ResumeThread.assert_not_called()
        a.TerminateProcess.assert_called_once_with(222,1)
        a.TerminateJobObject.assert_called_once()
        self.assertEqual(a.CloseHandle.call_count,3)

    def test_failed_resume_terminates_assigned_job(self):
        a=self.fake_api("resume")
        args,cwd=self.arguments()
        with self.assertRaisesRegex(OSError,"could not resume"):
            mod.ContainedProcess(a).start(args,cwd)
        a.AssignProcessToJobObject.assert_called_once()
        a.TerminateJobObject.assert_called_once()
        a.TerminateProcess.assert_not_called()

    def test_failed_create_releases_private_job(self):
        a=self.fake_api("create")
        args,cwd=self.arguments()
        with self.assertRaisesRegex(OSError,"process creation failed"):
            mod.ContainedProcess(a).start(args,cwd)
        a.AssignProcessToJobObject.assert_not_called()
        a.CloseHandle.assert_called_once_with(111)

    def test_failed_job_limit_prevents_process_creation(self):
        a=self.fake_api("job")
        args,cwd=self.arguments()
        with self.assertRaisesRegex(OSError,"kill-on-close"):
            mod.ContainedProcess(a).start(args,cwd)
        a.CreateProcessW.assert_not_called()

    def test_failed_job_termination_never_reports_success(self):
        api=self.fake_api()
        api.TerminateJobObject.return_value=0
        args,cwd=self.arguments()
        p=mod.ContainedProcess(api).start(args,cwd)
        with self.assertRaisesRegex(OSError,"private job termination API failed"):
            p.close()
        self.assertTrue(p.disposed)
        self.assertNotIn("private_job_terminated",p.events)
        self.assertIn("job_handle_closed",p.events)
        self.assertEqual(api.CloseHandle.call_count,3)

    def test_unobserved_child_exit_is_a_hard_cleanup_failure(self):
        api=self.fake_api()
        api.WaitForSingleObject.return_value=mod.WAIT_TIMEOUT
        args,cwd=self.arguments()
        p=mod.ContainedProcess(api).start(args,cwd)
        with self.assertRaisesRegex(OSError,"private child exit not observed"):
            p.close()
        self.assertTrue(p.disposed)
        api.TerminateJobObject.assert_called_once()

    def test_unassigned_child_termination_failure_is_reported(self):
        api=self.fake_api("assign")
        api.TerminateProcess.return_value=0
        args,cwd=self.arguments()
        with self.assertRaisesRegex(OSError,"unassigned child termination failed"):
            mod.ContainedProcess(api).start(args,cwd)
        api.ResumeThread.assert_not_called()
        api.TerminateJobObject.assert_called_once()

    def test_invalid_arguments_rejected_without_launch(self):
        a=self.fake_api()
        p=mod.ContainedProcess(a)
        with self.assertRaises(ValueError):
            p.start(["relative.exe","-B"],os.path.abspath("."))
        a.CreateJobObjectW.assert_not_called()

    def test_reusing_instance_is_prohibited(self):
        a=self.fake_api()
        args,cwd=self.arguments()
        p=mod.ContainedProcess(a).start(args,cwd)
        with self.assertRaisesRegex(RuntimeError,"cannot be reused"):
            p.start(args,cwd)
        p.close()

    def test_static_scope_excludes_generic_kill_or_live_runtime(self):
        contents=FILE.read_text(encoding="utf-8")
        for needle in ("taskkill","os.kill(","127.0.0.1:8766",
                       "relay-control.ps1","firefox.exe"):
            self.assertNotIn(needle,contents)
        self.assertIn("CREATE_SUSPENDED",contents)
        self.assertIn("AssignProcessToJobObject",contents)

if __name__=="__main__":unittest.main()
