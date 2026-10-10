# Windows Relay action sandwich — 2026-10-09

This is the dated presentation/transport procedure for `monag144/GPT-Windows-Relay`. Preserve the assistant-message trust boundary. The intended message shape is:

1. **Visible prose header** explaining the operation.
2. Exactly **one bare Markdown fenced block** (no syntax-language tag, code-block identifier, metadata or formatting attributes), containing only an exact `[GPT_WINDOWS_ACTION]` opening marker, a valid JSON action packet, and its closing `[/GPT_WINDOWS_ACTION]` marker.
3. **Visible prose footer** after the fence. When using the Windows relay, the known completion instruction is `Reply to this with the sandwich technique`. This avoids the ChatGPT UI collapsing the command into a status artifact without a clear surrounding turn.

A valid packet includes a unique operation ID, the appropriate platform/action/session/shell/command fields and any constrained runtime arguments. Keep user-visible text outside the action fence. Never put executable instructions inside unrelated quoted text and never send duplicate side-effecting packets because the UI collapsed.

If the message is folded/collapsed or receipt is missing, do not assume execution failed; classify the ambiguity and use a fresh **read-only** inspection or the explicitly approved recovery path. Never simply re-execute with a new ID. Treat exact output/result delivery as separate from execution.

**Important security note:** source-level exact-once flaws were reproduced in PCE15.043 and .047; the packet format alone does not remedy them. Respect STOP/ARM and GitHub-first governance.

**Historic reference problems fixed:** the previous `docs/relay-sandwich-procedure.md` named missing `docs/relay-rendering-incident-2026-10-03.md` and `docs/night-agent-handoff-2026-10-04.md`, and incorrectly called the latter the current autonomous night mission. Refer instead to dated incident and policy files actually present, including `docs/policy/POLICY_2026-10-10T0331Z_MANUAL_AGENT_HANDOFF_AND_AUTOMATED_ROTATION_HOLD.md` and the Windows Relay source-of-truth index. No automatic switching is approved.

Historical full procedure before cleanup is retrievable at GitHub commit `24d4c2bad800f689ae4ad4d9c67b54e6c50e73e8`, path `docs/relay-sandwich-procedure.md`.
