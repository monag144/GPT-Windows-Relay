# Windows Relay GitHub tool-approval behavior — 2026-10-11

**Operator-authorized behavior in prior conversation; source implementation present, actual loaded Firefox behavior still unverified.**

The current WIP `windows-relay/extension-persistent/content.js` implements a narrow GitHub permission-prompt detector near lines 2300–2384. The marked block `GPT_CHATGPT_GITHUB_APPROVAL_AUTOCLICK_V1` can select the persistent permission choice on a recognized prompt. Its matching conditions inspect provider name, precise prompt text, the expected set of choices, visibility/disabled state, scroll position and operator pause. The code emits `chatgpt_tool_approval_autoapproved` and uses a short repeated-prompt suppression interval.

**Operator authorization recovered from earlier conversation context:** The user explicitly accepted/requested this narrowly scoped behavior on **2026-10-06 at approximately 02:57 UTC (October 5 Pacific time)**: when the managed ChatGPT conversation is already at the bottom and the **exact GitHub approval card** appears, automatically select **“Always allow”**. The October 6 follow-up also specified the exact “Allow ChatGPT to use GitHub?” prompt and expected choices (“Always allow”, “Deny”, “Allow once”), while excluding generic/non-GitHub approvals. An earlier engineering summary reported an implementation and zero witnessed auto-click events. No later revocation was found in the retrieved conversation history. This is historical conversation evidence, **not proof of any extension being loaded now or of an actual click occurring**.

`windows-relay/tests/test_hud.py::test_github_approval_autoclick_is_exact_and_bottom_gated` checks static source fragments; it is not a live permission confirmation or an actual browser-click acceptance test.

**Reconciliation:** Preserve this specifically authorized narrow GitHub behavior unless the operator changes their instruction. Verify loaded Firefox extension identity from `about:debugging` and review actual browser activity before asserting it is active. Behavior tests should cover other providers, incomplete prompts, offscreen or disabled choices, paused state and repeated prompts. Document any future authorization decision separately.

No Firefox permissions, extensions, or runtime approval settings were modified by this source-evidence record.
