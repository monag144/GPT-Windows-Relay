# Incident — semantic successor rotation: editor draft and checkpoint synchronization

UTC 2026-10-09T00:44Z. Canonical repository monag144/GPT-Windows-Relay, branch pce11/one-click-go-recovery-and-doc-hygiene. STATUS: ROTATION BLOCKED; NO CLICK OR HANDOFF at latest attempt.

## Facts from durable results

- PCE11.035 first relay packet GOVERNANCE_BLOCKED before execution because previous five-slot audit .030–.034 was committed to GitHub but not yet pulled to Windows. The mandatory local pre-dispatch guard blocked the packet that was intended to pull. Recovered with distinct, unnumbered governance-only action AGENT011-GOVERNANCE-AUDIT-SYNC-030-034-20261008T2303Z (git merge --ff-only to 7732282784d21f3eaea2e6cb417b6bfeb567255e and engineering_preflight(ROOT,35,series=11) verified). No replay of originally blocked .035.

- PCE11.035 unique new packet did read-only Firefox UIA metadata: one visible enabled editable Ask ChatGPT control class non-ProseMirror, one offscreen enabled ProseMirror edit. Root cause ROTATION_COMPOSER_COUNT_0 was a too-restrictive class predicate; minimal GitHub-first worker correction requires exactly one visible enabled writable named edit.

- PCE11.036: newly-added static test failed before worker launch with ValueError on brittle newline within Python substring marker. GitHub-first test fixed to match sole marker; worker unchanged.

- PCE11.037: targeted composer tests 8/8, URLbar tests 2/2, launch tests 1/1, full Windows 536/536, full consumer 123/123, JavaScript syntax 5/5 and scanner mirrors identical. A new one-shot CREATE_NO_WINDOW worker PID 2092 reached WAITING_FOR_SOURCE_RESULT. This proves only worker startup.

- PCE11.038: durable terminal worker receipt HALT_BEFORE_CLICK SOURCE_COMPOSER_HAS_DRAFT; click_invoked=false; send_invoked=false; handoff_visible=false; distinct_new_conversation=false. No PCE12 transfer.

- PCE11.039: read-only scoped UIAutomation metadata found both Ask ChatGPT edit values length 12, non-whitespace and unequal to known placeholders Ask ChatGPT, Ask anything, Message ChatGPT. Values were not printed or persisted. Exactly one editor visible writable, the ProseMirror alternative offscreen. Neither editor was altered. Treat the content as potential genuine unsent draft.

## Safety/rollback

Do not clear, overwrite, or transmit the 12-character draft, and do not bypass the draft-block check in the original tab. STOP/owner/mission exact-once checks must persist. Live Client/Relay/extension/content.js last verified SHA256 34500934b214423afc2d3c267877a961cd0ec46521e5860ed149502d7f4e2ae5, backed-up nine original files, candidate stages .009/.016 and 2532-file broken ZIP remain protected. No 12/24 hour canary or release promotion. User forwards normal relay packets; no unusual manual rescue.

## Follow-up

Complete five-slot audit .035–.039 and 20-slot review .020–.039 on canonical GitHub before PCE11.040. Since governance checks fire before action execution, ff-only sync both checkpoint commits by unique unnumbered governance-only packet before .040. For eventual PCE12 successor consider a separate Firefox tab to preserve source draft; this is only an unproven design proposal. First gather positively scoped tab/new-chat accessibility evidence, tests and rollback; never blindly click or repeat uncertain submission.

COMPLETE incident classification. Rotation remains BLOCKED until separate-tab safety validated.
