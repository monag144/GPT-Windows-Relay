# Windows Relay GitHub tool-approval behavior — 2026-10-11

**Source-level observation, not proof of enabled runtime behavior or current operator preference.**

The current WIP `windows-relay/extension-persistent/content.js` implements a narrow GitHub permission-prompt detector near lines 2300–2384. The marked block `GPT_CHATGPT_GITHUB_APPROVAL_AUTOCLICK_V1` can select the persistent permission choice on a recognized prompt. Its matching conditions inspect provider name, precise prompt text, the expected set of choices, visibility/disabled state, scroll position and operator pause. The code emits `chatgpt_tool_approval_autoapproved` and uses a short repeated-prompt suppression interval.

The source comment describes the behavior as previously operator-authorized. That description establishes **the developer's recorded assumption only**. The reviewed code and test files do not establish when the operator agreed, which Firefox add-on is currently loaded, or whether the automation has fired in the live application.

`windows-relay/tests/test_hud.py::test_github_approval_autoclick_is_exact_and_bottom_gated` checks static source fragments; it is not a live permission confirmation or an actual browser-click acceptance test.

**Reconciliation:** Capture the current operator's explicit preference for this automation, including its exact scope. Verify loaded Firefox extension identity from `about:debugging` and review actual browser activity before asserting it is active. Behavior tests should cover other providers, incomplete prompts, offscreen or disabled choices, paused state and repeated prompts. Document any future authorization decision separately.

No Firefox permissions, extensions, or runtime approval settings were modified by this source-evidence record.
