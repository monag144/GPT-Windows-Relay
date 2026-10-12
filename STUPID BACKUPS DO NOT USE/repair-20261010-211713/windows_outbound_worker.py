from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

from firefox_adapter import normalize_conversation_url, resolve_conversation_tab, send_relay_result
from windows_relay import outbound_result_file

GPT_WINDOWS_DORMANT_OUTBOUND_WORKER_V1=True
TERMINAL_SENDER_STATES={"PRE_SUBMIT_FAILED","SUBMITTED","SUBMIT_UNCERTAIN"}

class WindowsOutboundWorker:
    def __init__(
        self,
        state,
        conversation_url: str,
        *,
        profile_path: str | None = None,
        pause_path: str | Path | None = None,
        resolver: Callable[...,dict[str,Any]] = resolve_conversation_tab,
        sender: Callable[...,dict[str,Any]] = send_relay_result,
        result_file_getter: Callable[...,str] = outbound_result_file,
    ):
        self.state=state
        self.conversation_url=normalize_conversation_url(conversation_url)
        self.profile_path=profile_path
        self.pause_path=Path(pause_path) if pause_path is not None else Path(__file__).with_name('.relay-paused')
        self.resolver=resolver
        self.sender=sender
        self.result_file_getter=result_file_getter
        self.transaction_lock=threading.Lock()

    def _paused(self) -> bool:
        return self.pause_path.exists()

    def _preclaim_failure(self, aid: str | None, reason: str) -> dict[str,Any]:
        return {"status":"PRECLAIM_FAILED","id":aid,"reason":reason}

    def run_once(self) -> dict[str,Any]:
        # At most one packet per call. No loop/thread is started here.
        with self.transaction_lock:
            if self._paused():
                return {"status":"PAUSED","id":None}

            ids=self.state.list_claimable_outbound_ids()
            if not ids:
                return {"status":"IDLE","id":None}
            aid=ids[0]

            delivery=self.state.outbound_lookup(aid)
            if not isinstance(delivery,dict):
                return self._preclaim_failure(aid,"delivery_unavailable")
            if delivery.get("phase") not in {"READY","PRE_SUBMIT_FAILED"}:
                return self._preclaim_failure(aid,"delivery_not_claimable")
            if delivery.get("has_attachments") is not False:
                return self._preclaim_failure(aid,"attachments_unsupported")

            try:
                result_file=self.result_file_getter(self.state,aid)
            except Exception as exc:
                return self._preclaim_failure(aid,f"wire_validation:{type(exc).__name__}")

            try:
                target=self.resolver(self.conversation_url,profile_path=self.profile_path)
            except Exception as exc:
                return self._preclaim_failure(aid,f"target_resolution:{type(exc).__name__}")

            if not isinstance(target,dict) or target.get("conversation_url")!=self.conversation_url:
                return self._preclaim_failure(aid,"target_identity_invalid")
            tab_name=target.get("tab_name")
            firefox_pid=target.get("firefox_pid")
            if not isinstance(tab_name,str) or not tab_name:
                return self._preclaim_failure(aid,"target_tab_invalid")
            if isinstance(firefox_pid,bool) or not isinstance(firefox_pid,int) or firefox_pid<=0:
                return self._preclaim_failure(aid,"target_pid_invalid")

            if self._paused():
                return {"status":"PAUSED","id":aid}
            if aid not in self.state.list_claimable_outbound_ids():
                return self._preclaim_failure(aid,"claimability_changed")

            try:
                self.state.claim_outbound_delivery(aid)
            except Exception as exc:
                return self._preclaim_failure(aid,f"claim:{type(exc).__name__}")

            try:
                outcome=self.sender(
                    result_file,
                    aid,
                    tab_name,
                    self.conversation_url,
                    firefox_pid=firefox_pid,
                    profile_path=self.profile_path,
                )
                phase=outcome.get("state") if isinstance(outcome,dict) else None
                if phase not in TERMINAL_SENDER_STATES:
                    raise RuntimeError("invalid sender terminal state")
            except Exception as exc:
                try:
                    self.state.finish_outbound_delivery(aid,"SUBMIT_UNCERTAIN")
                except Exception as finish_exc:
                    return {"status":"SUBMITTING_UNRESOLVED","id":aid,"reason":f"sender:{type(exc).__name__};finish:{type(finish_exc).__name__}"}
                return {"status":"SUBMIT_UNCERTAIN","id":aid,"reason":f"sender:{type(exc).__name__}"}

            try:
                self.state.finish_outbound_delivery(aid,phase)
            except Exception as exc:
                return {"status":"SUBMITTING_UNRESOLVED","id":aid,"reason":f"finish:{type(exc).__name__}"}
            return {"status":phase,"id":aid,"sender":outcome}
