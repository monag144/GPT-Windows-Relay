"""Mock Win32 HTTP-host ancestry and exact private Job membership; no process launches."""
import ctypes
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock

MOD=Path(__file__).resolve().parents[1]/"tools"/"pce11_private_host_identity.py"
spec=importlib.util.spec_from_file_location("pce11_private_host_identity",MOD)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class HostOwnershipTests(unittest.TestCase):
    def mocks(self,pid=2002,launcher=1001,parent=1001,member=True,image="C:/Python313/python.exe"):
        k=Mock()
        n=Mock()
        k.OpenProcess.return_value=77
        k.GetProcessId.return_value=pid
        k.CloseHandle.return_value=1
        k.WaitForSingleObject.return_value=0
        def in_job(handle,job,out):
            self.assertEqual(handle,77)
            self.assertEqual(job,555)
            out._obj.value=bool(member)
            return 1
        k.IsProcessInJob.side_effect=in_job
        def basic(handle,klass,info,size,written):
            self.assertEqual(klass,0)
            info._obj.UniqueProcessId=pid
            info._obj.InheritedFromUniqueProcessId=parent
            written._obj.value=ctypes.sizeof(m.PROCESS_BASIC_INFORMATION)
            return 0
        n.NtQueryInformationProcess.side_effect=basic
        def executable(handle,flags,buff,size):
            buff.value=image
            size._obj.value=len(image)
            return 1
        k.QueryFullProcessImageNameW.side_effect=executable
        return k,n

    def test_direct_venv_child_attested_and_exit_proven(self):
        k,n=self.mocks()
        proof=m.PrivateHost(2002,1001,555,k,n)
        self.assertTrue(proof.verified)
        self.assertTrue(proof.job_member)
        self.assertEqual(proof.parent_pid,1001)
        self.assertEqual(proof.host_image,"C:/Python313/python.exe")
        self.assertTrue(proof.wait_for_exit())
        proof.close()
        self.assertTrue(proof.exit_observed)
        k.CloseHandle.assert_called_once_with(77)

    def test_original_launch_process_can_host_directly(self):
        k,n=self.mocks(pid=1001,parent=999)
        proof=m.PrivateHost(1001,1001,555,k,n)
        self.assertTrue(proof.verified)
        proof.wait_for_exit();proof.close()

    def test_foreign_job_host_rejected_and_handle_released(self):
        k,n=self.mocks(member=False)
        with self.assertRaisesRegex(RuntimeError,"exact private Job"):
            m.PrivateHost(2002,1001,555,k,n)
        k.CloseHandle.assert_called_once_with(77)

    def test_unrelated_parent_rejected_and_handle_released(self):
        k,n=self.mocks(parent=3333)
        with self.assertRaisesRegex(RuntimeError,"direct child"):
            m.PrivateHost(2002,1001,555,k,n)
        k.CloseHandle.assert_called_once_with(77)

    def test_pid_reuse_or_handle_mismatch_rejected(self):
        k,n=self.mocks()
        k.GetProcessId.return_value=9009
        with self.assertRaisesRegex(RuntimeError,"identity changed"):
            m.PrivateHost(2002,1001,555,k,n)
        k.CloseHandle.assert_called_once_with(77)

    def test_invalid_http_executable_rejected(self):
        k,n=self.mocks(image="C:/Users/somewhere/unknown.exe")
        with self.assertRaisesRegex(RuntimeError,"not Python"):
            m.PrivateHost(2002,1001,555,k,n)
        k.CloseHandle.assert_called_once_with(77)

    def test_unobserved_exit_never_counts_as_clean(self):
        k,n=self.mocks()
        k.WaitForSingleObject.return_value=0x102
        proof=m.PrivateHost(2002,1001,555,k,n)
        with self.assertRaisesRegex(RuntimeError,"did not exit"):
            proof.wait_for_exit()
        self.assertFalse(proof.exit_observed)
        proof.close()

    def test_missing_or_non_integer_pids_never_open_process(self):
        k,n=self.mocks()
        with self.assertRaisesRegex(RuntimeError,"non-integer"):
            m.PrivateHost("2002",1001,555,k,n)
        with self.assertRaisesRegex(RuntimeError,"non-integer"):
            m.PrivateHost(2002,True,555,k,n)
        k.OpenProcess.assert_not_called()

    def test_identity_api_failure_fails_closed(self):
        k,n=self.mocks()
        n.NtQueryInformationProcess.return_value=0xC0000001
        n.NtQueryInformationProcess.side_effect=None
        with self.assertRaisesRegex(OSError,"ancestry query failed"):
            m.PrivateHost(2002,1001,555,k,n)
        k.CloseHandle.assert_called_once_with(77)

if __name__=="__main__":unittest.main()
