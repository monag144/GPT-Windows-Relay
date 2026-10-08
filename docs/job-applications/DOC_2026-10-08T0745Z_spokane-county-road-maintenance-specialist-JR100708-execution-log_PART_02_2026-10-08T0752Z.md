# Archived source fragment 2/6 — 2026-10-08T0752Z

- For this Workday source control, the edit value may be sufficient even when the custom suggestion-row checked state does not update.
- Do not keep mutating the widget speculatively; use Workday's own form validation as the authority.
- Next action: invoke Save and Continue. If the required-source validation clears and the application advances, preserve this as the preferred fallback for this control class. If validation persists, inspect the exact post-submit state again.


## PCENG4-SPOKANE-026 — Plain source edit value rejected by Workday validation

Result: **OK diagnostic; Step 1 still blocked**.

- Source edit contained `Other` before Save and Continue.
- Workday still returned the required-field error for How Did You Hear About Us.
- Therefore a raw edit value is not equivalent to committing a valid source selection.
- The observed Step 2 marker was only the application's navigation/step indicator; the active form remained My Information.
- No experience data was entered.

Revised interpretation:
- Workday requires its internal source-selection state, not merely visible/edit text.
- Before more physical clicks, verify foreground window state and perform UI Automation hit-testing across the visible Other row to confirm the actual element beneath candidate click coordinates.


## PCENG4-SPOKANE-027 — Hit testing exposed the real Workday option surface

Result: **OK diagnostic**.

- Firefox was already the foreground window.
- The accessible `Other not checked` ListItem spans the visible row, but point hit-testing showed the clickable interior resolves to a nested Group whose AutomationId begins `promptOption-`.
- The center of the row hit this `promptOption` Group, not the ListItem wrapper.
- Edge areas resolve to surrounding Firefox/Workday container Groups.

Engineering finding:
- The Workday ListItem is an accessibility wrapper; the inner `promptOption-*` Group is the likely React event target.
- Generated promptOption IDs may also be dynamic, so select it by containment beneath the semantic Other row rather than persisting the UUID.
- Next attempt should invoke the nested Group itself and verify selected-token/checked state before advancing.


## PCENG4-SPOKANE-028 — Nested promptOption Invoke also ignored

Result: **OK diagnostic; source remains unset**.

- Located the nested Workday `promptOption-*` Group inside the semantic `Other not checked` row.
- The Group exposed Invoke and accepted the Invoke call.
- Workday still reported `Other not checked`, no selected token appeared, and required-source validation remained active.
- SMS consent remained unchanged; Save and Continue was not invoked.

Implication:
- Firefox accessibility actions are being accepted at multiple exposed layers without dispatching the React state transition this widget requires.
- Next diagnostic should inspect the row in Raw View, including hidden descendants, classes, patterns and bounding rectangles, to find any native checkbox/input node flattened out of Control View.


## PCENG4-SPOKANE-029 — Raw View identified separate right-side option indicator

Result: **OK diagnostic**.

Raw View of the semantic `Other not checked` row showed:
- outer ListItem wrapper;
- main prompt-option Group containing the visible `Other` label;
- a separate sibling Group, approximately 24×24 pixels, aligned at the far right edge of the row.

No native CheckBox element exists beneath the row.

Interpretation:
- Prior interactions targeted the row body / label surface.
- The isolated right-side 24×24 Group is the strongest candidate for Workday's actual checked-state indicator and event target.
- Next action should target that indicator specifically, preferably by semantic containment and geometry rather than a generated ID, then rebuild the tree and verify the row changes from `not checked`.


## PCENG4-SPOKANE-030 — Dedicated option indicator also ignored

Result: **OK diagnostic; source remains unset**.

- The separate right-side 24x24 option indicator was targeted directly.
- Both its exposed Invoke action and a physical mouse click at its center were dispatched.
- Workday still reported the source option as not checked.
- Source edit remained blank.
- SMS consent remained unchanged and Save and Continue was not invoked.

Revised root-cause hypothesis:
- Prior source-text attempts used UI Automation ValuePattern.SetValue.
- In browser-based React controls, ValuePattern can update the accessibility/edit value without generating the native keyboard/input/change events that the application state machine expects.
- Therefore subsequent option actions may have been operating against a widget whose internal search/input state was never actually changed.
- Next recovery should use real keyboard input: focus source edit, Ctrl+A, type Other through SendKeys, wait for React input handling, then Down+Enter and audit the token/checked state.


## PCENG4-SPOKANE-031 — Required source successfully committed via native keyboard events

Result: **OK; required-source validation cleared**.

Successful interaction sequence:
1. Focus the Workday source edit.
2. Clear it using native keyboard input.
3. Type `Other` through genuine keystrokes.
4. Wait for Workday/React to process the input.
5. Press Down, then Enter.

Verification:
- Before commit, the edit value was `Other` and the suggestion appeared as `Other not checked`.
- After Down+Enter, the edit value returned to blank.
- The `Other not checked` suggestion disappeared.
- Required-source validation markers dropped to zero.
- SMS consent remained unchanged.
- Save and Continue was not invoked in this operation.

Root cause confirmed:
- UI Automation `ValuePattern.SetValue` was insufficient for this Workday React search/multi-select because it did not trigger the native browser input events Workday requires.
- Native keystrokes successfully drove the component's internal state.

Reusable Workday rule:
- For React search/select controls that ignore Invoke/SelectionItem/click actions, use genuine keyboard input to generate browser input/change events, then commit the filtered option with native navigation keys.
- A blank edit field after commit can be correct when the typed search text has been consumed into Workday's internal selection state; validate via disappearance of required errors and option-state changes rather than edit text alone.


## PCENG4-SPOKANE-033/034 — Exact Work Experience instruction recovered

The Work Experience section contains the posting-specific instruction:

`REQUIRED: Add the following to the Role Description field`
- `Duties`
- `Reason for Leaving`

Automation boundary:
- Duties may be populated only from supported employment records.
- Reasons for leaving are not established by the current canonical employment/source documents for most roles and must not be invented.
- Before entering employment history, map the blank Work Experience record schema and determine whether Role Description is mandatory for every record and whether any additional fields are required.


## PCENG4-SPOKANE-038 — Education degree taxonomy mapped

Workday Education fields:
- School or University
- Degree (required)
- Field of Study
- Overall Result (GPA)

Degree choices include:
- GED
- High School Diploma
- AA / AS
- BA / BS
- graduate/professional degrees
- Other (Not Listed)

Important boundary:
- There is no explicit `some college` or `no degree` choice.
- Do not represent college coursework as an AA/AS/BA/BS.
- The confirmed high-school credential can be entered safely as **High School Diploma**.
- GPA and Field of Study should remain blank unless supported or required.
- Any incomplete college coursework should use only a truthful non-degree representation if the form later requires it; never invent a degree.


## PCENG4-SPOKANE-039 — Partial Education write; non-idempotent Expand call

Result: **COMMAND_FAILED after partial mutation**.

Confirmed mutation:
- School/University field was populated from the confirmed high-school record.

Failure:
- Calling `ExpandCollapsePattern.Expand()` on the Degree control threw `InvalidOperationException`.
- The Degree menu had been opened by the preceding mapping operation and may already have been expanded.

Mutation boundary:
- School name written.
- Degree not selected by this operation.
- Field of Study and GPA untouched.
- No Add Another or Save and Continue action.

Reusable rule:
- Treat Workday Expand/Collapse controls as stateful and non-idempotent.
- Read `Current.ExpandCollapseState` before calling Expand/Collapse; if already expanded, reuse the open menu instead of invoking Expand again.


