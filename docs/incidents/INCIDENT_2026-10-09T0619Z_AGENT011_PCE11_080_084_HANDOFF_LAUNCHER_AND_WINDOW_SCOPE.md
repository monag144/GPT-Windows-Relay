# Incident: PCE11.080–.084 PCE12 handoff not delivered

**Status:** OPEN — no PCE12 user-turn proof. **Window:** 2026-10-09T06:03–06:17 UTC. **Severity:** agent handoff failure / repeated engineering operations, not user-message duplicate. **Repository:** monag144/GPT-Windows-Relay, canonical pce11 recovery branch.

**Symptom and positive evidence:** .080 initially blocked by missing local audit/review, then governance-only sync PASS. .080 second launcher NameError `worker_file`; .081 incorrect hardcoded control SHA `CONTROL_DRIFT`; .082 FileNotFound `PCE11_080_PCE12_PAYLOAD.txt`. .083 rebuilt and syntax-checked 8,642-character payload, launched worker PID 11900. Unique immutable receipt phase `HALT_UNCERTAIN_NO_RETRY`, error `FIREFOX_NOT_ON_NEW_CHAT`, all UI effects false (composer click, paste, Send). .084 read-only confirmed failure. The actual chat handoff was **not** delivered. Separately .076 did successfully semantically open New Chat in original tab, no submission; .079 clipboard payload was verified.

**Root cause:** repeated inline Python shell payload construction and false dependency upon files never created after earlier blocked operations, followed by an overly broad Firefox window gate asserting **every** visible Firefox window is on `chatgpt.com/`. The browser target must be determined by selected tab count/identity, not by using home-page URL as a global Firefox condition. A distinct one-tab Firefox window may be elsewhere, without invalidating a pinned 11-tab target.

**User impact:** delayed new chat takeover and repeated blocked results. User has explicitly directed assistant to issue actual UI commands and not shift paste/Send work back to operator. No duplicate send occurred; .083 proves it stopped before any click, paste or Send.

**Containment/rollback:** previous workers' unique receipts are no-retry; no source PCE11 draft or window change from .083; no production extension deploy. Current GitHub branch has audit/review, old handoff and helper sources. Preserve all receipts/logs; don't replay .083 or click New Chat. Read-only two-window diagnostic at .085 after governance sync; gate new worker on exactly one correct source-window chat home with current STOP epoch and empty writable composer. Do not disclose user draft or payload in diagnostic.

**Lessons:** check local artifact existence before relying on it; pre-compile worker and test source offline; don't blanket-fail unrelated Firefox windows; enforce immutable one-action semantics and positive message bubble proof.
