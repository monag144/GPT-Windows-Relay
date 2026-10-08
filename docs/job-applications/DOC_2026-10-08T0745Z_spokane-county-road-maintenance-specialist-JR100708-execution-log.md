# Spokane County JR100708 — Execution Log — 2026-10-08T0745Z

This companion log records reusable automation behavior and mission progress without applicant PII. Applicant facts remain in the local canonical profile and live application.

## Operations 010-018 recap

- Candidate-account creation initially failed because this Windows PowerShell/.NET runtime lacked the expected static RNG helper. No form mutation occurred before that failure.
- Recovery used a compatibility-safe local random generator; the candidate session was established successfully without exposing secret material in relay output or GitHub.
- Workday advanced directly into the application after account setup.
- Firefox window titles can lag Workday SPA state; document content and controls are authoritative.
- Document-scoped UI Automation is the preferred Workday inspection method because it avoids hidden accessibility content from other Firefox tabs.
- Workday exposes a robot-only honeypot field. Automation must always detect and leave such controls blank.
- Step 1 of 6 is My Information.
- Generic Yes/No radios were resolved through their ancestor group label before answering.
- A PowerShell helper named R collided with the built-in Invoke-History alias. Reusable rule: use descriptive helper names.
- One text-field write produced a false-negative immediate readback; a later audit proved the value persisted. Workday fields may debounce asynchronously, so fresh audits are preferred over sub-second equality checks.
- State and phone-device selectors were mapped before use.
- Optional sourcing/referral fields remain blank when provenance is unknown rather than receiving guessed values.
- A tokenized phone-country selector exposes its selected value through a token/list element while the backing edit control is blank. Audit both representations.
- My Information is now populated and audited from the canonical profile. It has not yet been advanced with Save and Continue.

## Next

Invoke Save and Continue. If Workday reports validation errors, map them precisely. Otherwise inventory step 2 of 6, My Experience, before entering employment data.


## PCENG4-SPOKANE-019 — Step 1 validation exposed required source field

Result: **OK; validation blocked advancement**.

- Save and Continue was invoked from My Information.
- Workday returned: `The field How Did You Hear About Us? is required and must have a value.`
- All previously populated required identity/contact fields remained present.
- No Step 2 data was entered.
- Workday also exposed optional consent language for periodic automated employment-related messages; no consent selection was made.

Source-field decision:
- The applicant supplied the target requisition URL directly in this automation session.
- There is no supported evidence that the opening was discovered through a job board, referral, staffing agency, social media, internal source, career center, or job fair.
- Because Workday requires a category, select **Other** as the least-assumptive category rather than inventing a specific source.
- If Workday asks for a free-text or child source after selecting Other, describe only the known fact (direct job link supplied by applicant) without naming an unsupported discovery channel.

Consent rule:
- Do not opt into optional automated-message/marketing consent merely to advance an application.
- Leave optional consent controls unselected unless the applicant explicitly opts in or Workday proves they are required.


## PCENG4-SPOKANE-020 — Required source selector did not commit on first attempt

Result: **OK diagnostic, selection did not persist**.

- Attempted to select source category **Other**.
- Workday still exposed the option as `Other not checked`.
- Required-field validation remained active.
- Therefore the attempted SelectionItem/Invoke path did not commit the source value.
- Optional SMS consent control was mapped and remains **Off**.
- No consent was granted and Save and Continue was not invoked.

Reusable rule:
- Some Workday multi-select/search-source menu items visually resemble list items but do not commit through assumed SelectionItem semantics.
- After any selector action, verify the option's checked state and/or the field token/value before treating it as selected.
- If state remains `not checked`, inspect supported patterns and use the option's native toggle/invoke behavior.


## PCENG4-SPOKANE-021 — Source option Invoke still did not commit

Result: **OK diagnostic; source remains unselected**.

- Reopened the required source selector and targeted the exact Workday menu item for **Other**.
- The option exposed Invoke as its supported action, but invoking it did not change the checked state.
- Verification still showed `Other not checked`.
- The source edit value remained blank.
- SMS consent remained unchanged and Save and Continue was not invoked.

Engineering consequence:
- Do not equate a supported UI Automation Invoke pattern with a successful Workday selection.
- The next diagnostic should inspect the Other option's descendants, ancestors, supported patterns and bounding rectangle to determine whether Workday expects interaction with a nested checkbox/control or a physical row click.


## PCENG4-SPOKANE-022 — Native source-option inspection

Result: **OK; read-only aside from opening the selector**.

Exact Workday `Other` option:
- control type: `ControlType.ListItem`
- menu-item id: `menuItem-a2cb6f99ed251000906d46e6edb20000`
- accessible state: `Other not checked`
- enabled and visible
- supported patterns:
  - Invoke
  - SelectionItem
  - ScrollItem
- one child Group covering the same row; child supports Invoke and ScrollItem
- parent hierarchy includes a Workday List named `Options Expanded`

Important finding:
- Both semantic approaches already tried (SelectionItem and Invoke) failed to update Workday's React-controlled checked state despite the accessibility object claiming support.
- The row has a concrete visible bounding rectangle, so a physical mouse click on the row is the next appropriate browser-compatibility fallback.
- Any physical click must be followed by a fresh document-scoped state audit; never assume a click succeeded merely because it was dispatched.

No source value was committed during this diagnostic.


## PCENG4-SPOKANE-023 — Physical row click still did not commit source

Result: **OK diagnostic; required source still unset**.

- A real mouse click was dispatched to the visible center of the Workday `Other` source row.
- The option remained `Other not checked`.
- Required-field validation remained active.
- SMS consent remained unchanged.
- Save and Continue was not invoked.

New finding:
- After Workday rerendered the menu, the `Other` option received a different dynamic AutomationId.
- Therefore individual Workday menu-item IDs are not stable selectors across rerenders.
- Prefer semantic matching on the accessible option name plus parent-list context rather than persisting generated menu IDs.

Next fallback:
- focus the semantic `Other not checked` row and dispatch native keyboard activation (Space, then Enter only if needed);
- after each attempt, rebuild the document tree and verify checked/token state.


## PCENG4-SPOKANE-024 — Keyboard activation also failed

Result: **OK diagnostic; required source remains unset**.

Attempted native keyboard activation on the semantic `Other not checked` row:
- Space dispatched — no checked state
- Enter dispatched — no checked state
- Source backing edit remained blank
- SMS consent remained unchanged
- Save and Continue was not invoked

Interpretation:
- Workday's source control should no longer be treated as a conventional selectable list row.
- The control is exposed primarily as an Edit field (`source--source`) whose menu rows appear to be search/multi-select suggestions.
- Next strategy: drive the source field as a searchable input, enter `Other`, inspect the filtered options and commit through the input/search interaction rather than through the list item's advertised accessibility patterns.


## PCENG4-SPOKANE-025 — Source input successfully populated through searchable edit

Result: **OK; source edit now contains `Other`**.

- Directly populated the Workday source edit control with `Other`.
- The filtered suggestion row remained visible as `Other not checked`.
- Down+Enter did not create a selected token.
- Crucially, the backing source field now reports value `Other` instead of blank.
- SMS consent remained unchanged.
- Save and Continue was not invoked.

Interpretation:
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


## PCENG4-SPOKANE-039/040 — High-school education staged successfully

- School field populated from the confirmed high-school record.
- Degree = **High School Diploma**.
- Field of Study left blank.
- GPA left blank.
- Workday Degree control was already Expanded from the prior mapping step; calling Expand again caused an InvalidOperationException.
- Recovery used ExpandCollapseState first and then selected the existing High School Diploma option.
- Reusable rule: Workday expand/collapse operations must be state-aware.

College boundary:
- The applicant has supported college coursework but no confirmed college degree.
- Workday offers no explicit `some college/no degree` choice.
- Do not select AA/AS/BA/BS for incomplete coursework.


## PCENG4-SPOKANE-041 — Remaining Step 2 sections mapped

- Certifications: optional Add section.
- Languages: optional Add section.
- Skills: searchable `skills--skills` input.
- Resume: explicit instruction `Please attach your Resume` with `resumeAttachments--attachments` Select files control.
- No data changed.

Plan:
- Keep optional qualification sections conservative; do not invent formal credentials.
- Use supported, job-relevant skills only.
- Locate and inspect the best current resume available to the Windows application workflow before uploading.


## PCENG4-SPOKANE-042 — Local resume candidates located

Read-only search found multiple local transportation/logistics resumes, including:
- a recently modified transport resume;
- the preferred Logistics Resume Quick source copy;
- logistics/transportation variants;
- a manufacturing/machine-operator resume.

No upload was performed.

Selection rule:
- Do not choose a resume solely from filename or modification time.
- Compare actual content of the strongest transportation/logistics and machinery-oriented candidates against JR100708.
- Prefer the version that truthfully emphasizes CDL, tanker/material-handling, machinery/safety, local/field operations and transferable maintenance-related work without inventing named road-maintenance equipment experience.


## PCENG4-SPOKANE-043 — Resume content comparison

Compared actual text from four strong local candidates.

Rejected as-is:
- recently modified transport resume: contains multiple certification claims that are not currently safe to rely on;
- longer logistics/transportation resume: contains stale contact data and should not be uploaded unchanged.

Usable but suboptimal:
- Logistics Resume Quick: safe transportation-focused base, but does not foreground industrial machinery/material-handling experience and contains stale profile details;
- Manufacturing Machine Operator resume: strong machinery/safety/material-handling fit, but under-emphasizes the Class A/tanker/doubles transportation background central to JR100708.

Decision:
- create a targeted Road Maintenance Specialist resume from supported facts only, combining CDL/tanker/local operations, forklift/material handling, industrial machinery, safety, and equipment-check experience;
- do not claim experience with graders, pavers, plows, excavators, vactors, cranes, or other posting-specific machinery unless independently supported;
- do not include unverified formal certifications.


## PCENG4-SPOKANE-044 — Word COM available but authoring probe hung

Result: **TIMEOUT after Microsoft Word launched successfully**.

Observed before timeout:
- Word COM automation is installed and reachable.
- Microsoft Word reported version 16.0.
- The probe hung after application creation, before the temporary document test completed.

Safety/recovery:
- Do not continue relying on interactive Word COM for this application; a hidden first-run/template/modal state may be blocking document creation.
- Inspect any orphaned hidden WINWORD process without terminating a visible user Word session.
- Prefer direct DOCX generation with a non-interactive library such as python-docx if available locally.
- No resume was created and no Workday data changed.


## PCENG4-SPOKANE-045 — Direct DOCX toolchain check

- The only WINWORD process is hidden and began at the exact time of the timed-out COM probe; no visible Word window is associated with it.
- Python 3.13 is available, but `python-docx` is not installed.
- LibreOffice is not installed.
- The intended Generated Resumes destination exists.

Recovery decision:
- Do not install dependencies merely to complete this application.
- Generate a standards-compliant DOCX directly as an Open XML package using PowerShell/.NET, then validate ZIP structure and extracted document text before upload.
- The hidden WINWORD process from the probe can be left alone unless it interferes; do not terminate unrelated visible user processes.


## PCENG4-SPOKANE-046 — Targeted resume created but package validation failed

Result: **COMMAND_FAILED during validation after file creation**.

- A targeted Road Maintenance Specialist DOCX was written to the Generated Resumes workspace.
- Validation found that required Open XML parts were not addressable under their canonical ZIP entry names.
- The file must be treated as invalid and must not be uploaded in this state.
- Failure occurred before any Workday upload.
- Resume content should be preserved while repairing only the package entry paths, then revalidate the package structure and document XML/text.


## PCENG4-SPOKANE-047 — Targeted resume package repaired and validated

Result: **OK**.

- Repaired the generated DOCX package so all ZIP entries use canonical forward-slash Open XML paths.
- Required parts validated:
  - [Content_Types].xml
  - _rels/.rels
  - word/document.xml
  - word/styles.xml
  - word/_rels/document.xml.rels
- document.xml parses successfully.
- The package opens through the Windows OPC packaging API.
- Full text readback matches the intended targeted resume.
- No Workday upload occurred during validation.

Target resume:
`Jack Monaghan - Road Maintenance Specialist Resume.docx`

Content strategy:
- foreground Class A CDL, T/X endorsements, tanker/doubles, local freight, rear-dump assignments, material handling, forklift, industrial machinery, equipment checks, and safety;
- include only supported work history/training;
- make no claim of grader, plow, paver, excavator, crane, vactor, or other unsourced road-maintenance-machine experience.


## PCENG4-SPOKANE-048 — Resume file picker invoked; standard-dialog detector missed it

Result: **OK diagnostic; no upload completed**.

- Workday's `Select files` control was invoked.
- No visible top-level window with classic common-dialog class `#32770` was found.
- No file path was entered and no upload completed.

Interpretation:
- Do not assume the picker failed merely because `#32770` was absent.
- Firefox/Windows may expose the picker under a different top-level class or accessibility surface.
- Next diagnostic should enumerate all visible top-level windows and dialog-like descendants after the picker invocation, including their process IDs, classes, titles, and editable controls.


## PCENG4-SPOKANE-049 — UI Automation top-level enumeration went blind after picker invocation

Result: **OK diagnostic; no upload completed**.

- UI Automation returned zero visible top-level windows during the picker-identification pass.
- Therefore the absence of a classic file-dialog object cannot be treated as evidence that the picker is absent.
- No file path was entered and no upload completed.

Recovery:
- Bypass UI Automation top-level discovery and enumerate native HWNDs with user32 `EnumWindows`, recording owner process, class, title, visibility, enabled state, and foreground handle.
- Convert likely picker HWNDs back into AutomationElements only after native identification.


## PCENG4-SPOKANE-050 — Native picker enumeration script parse failure

Result: **COMMAND_FAILED before execution**.

- PowerShell parser rejected the `Sort-Object` expression used to order native window rows.
- No native window enumeration occurred.
- No UI action occurred.
- No file path was entered and no upload completed.

Recovery:
- rerun the same native HWND diagnostic with valid PowerShell sort syntax;
- preserve the read-only nature of the operation.


## PCENG4-SPOKANE-051 — Native HWND enumeration variable collision

Result: **COMMAND_FAILED before useful enumeration**.

- Foreground HWND was read successfully.
- The callback then attempted to assign to `$pid`, which collides case-insensitively with PowerShell's read-only automatic variable `$PID`.
- Enumeration aborted before picker identification.
- No UI action, file-path entry, or upload occurred.

Reusable rule:
- Avoid `pid` as a mutable PowerShell variable name; use explicit names such as `$processIdValue`.


## PCENG4-SPOKANE-052 — Native file picker identified

Result: **OK diagnostic**.

- Native HWND enumeration identified the foreground picker:
  - process: Firefox
  - class: `#32770`
  - title: `File Upload`
- The underlying Workday Firefox window is disabled while the modal picker is active.
- UI Automation from the native picker HWND exposes:
  - Shell Folder View
  - File name area
  - file-type selector
  - Open
  - Cancel
  - address/navigation controls
- No file path was entered and no upload completed.

Reusable rule:
- If the desktop UIA root fails to surface a modal picker, enumerate native HWNDs with user32 and convert the foreground HWND back into an AutomationElement.
- For a standard `#32770` file dialog, native keyboard access to the File name field is a robust fallback.


## PCENG4-SPOKANE-053 — Validated targeted resume uploaded successfully

Result: **OK**.

Workday verification after native file selection:
- exact attachment name visible: `Jack Monaghan - Road Maintenance Specialist Resume.docx`
- status visible: `Successfully Uploaded!`
- attachment-specific delete control visible
- file picker closed and focus returned to Firefox
- Save and Continue was not invoked

Reusable upload workflow:
1. Invoke Workday `Select files`.
2. If normal UIA desktop discovery misses the picker, identify foreground native HWND.
3. Confirm Firefox-owned `#32770` window titled `File Upload`.
4. Use native File name keyboard access, type the validated absolute path, press Enter.
5. Return to the Workday document and verify both exact filename and explicit successful-upload status before advancing.


## PCENG4-SPOKANE-054 — Skills taxonomy probe

Result: **OK; no skill selected**.

- Native-keyboard search for `Commercial` produced no matching accessible Workday skill options.
- The search input was cleared afterward and read back blank.
- No skill token was selected.
- Save and Continue was not invoked.

Decision:
- Do not force arbitrary or weakly matched skill tags merely to populate an optional section.
- Leave Skills blank unless the final Step 2 audit reveals a requirement or a clearly supported selectable taxonomy item.


## PCENG4-SPOKANE-055 — Final Step 2 completeness audit

Result: **OK; Step 2 appears complete and ready to advance**.

Verified:
- F|Staff current role fields are populated and persisted.
- Current-employment toggle is On; end-date controls are absent as expected.
- Role Description includes both Duties and Reason for Leaving.
- Northern Pacific High School is staged with High School Diploma selected.
- Optional Field of Study and GPA remain blank.
- Skills remains blank after the no-match taxonomy probe.
- Targeted resume filename is visible and Workday reports `Successfully Uploaded!`.
- `Save and Continue` is enabled.

Interpretation of education guidance:
- Workday displays `Please include your completed College/University and High School/GED Education`.
- The applicant has a completed high-school diploma but only non-degree college coursework.
- Do not invent or select a college degree merely to populate the section; omit incomplete college as a separate Workday education credential unless a later validation explicitly requires it.

Next:
- invoke Save and Continue;
- map the next page before answering questions;
- stop on unresolved high-stakes facts such as current CDL medical-card status, CDL restrictions, or current Washington driver-license status.


## PCENG4-SPOKANE-056 — Advanced to Application Questions

Result: **OK**.

- Step 2 Save and Continue succeeded.
- Current page heading: `Application Questions`.
- Workday exposes:
  - five required `Select One` buttons;
  - four text inputs;
  - Back and Save and Continue.
- No Application Questions answers were changed.
- No final submit occurred.

Important observation:
- ordinary visible-text enumeration did not expose the actual question prompts;
- questionnaire controls are identifiable by stable `primaryQuestionnaire--...` automation IDs, but their accessible names are generic.
- Next step must map each control to nearby ancestors/siblings/labels before answering.


## PCENG4-SPOKANE-057 — Application-question prompts mapped

Mapped questionnaire controls:

1. Are you currently employed by Spokane County? — required selector
2. Are you UNDER 18 years of age? — required selector
3. Can you, after employment, submit proof of your legal right to work in the United States? — required selector
4. Please list all of your current Certifications and Licenses and the issue date. — text
5. Do you have supervising/management experience? — required selector
6. Do you have relatives who are employed by Spokane County? (Information used for nepotism policy only) — required selector
7. Please include an alternate phone number to contact you, if applicable. — optional text
8. Please include any former last names, if applicable. — optional text
9. If you listed "Other" as your how did you hear about us, please state your referral source. — text

Planned truthful staging, subject to selector-option verification:
- current Spokane County employee: No;
- under 18: No;
- proof of legal right to work in U.S.: Yes;
- certifications/licenses: Class A CDL, T and X endorsements, with original issue date explicitly identified as 2018-08-30;
- supervisory/management experience: Yes;
- Spokane County relatives: No;
- alternate phone: blank because no alternate number is supplied;
- former last name: blank because none is supplied;
- referral source: Spokane County Careers website / direct job posting.

Do not add unsourced certifications or issue dates.


## PCENG4-SPOKANE-058 — Required selector options verified

Result: **OK; no answers changed**.

All five required Application Questions selectors expose only `Yes` / `No` choices:

- currently employed by Spokane County: Yes / No
- under 18: No / Yes
- can submit proof of legal right to work: Yes / No
- supervising/management experience: Yes / No
- relatives employed by Spokane County: Yes / No

Planned answers remain:
- Spokane County employee: No
- under 18: No
- proof of legal right to work: Yes
- supervisory/management experience: Yes
- Spokane County relatives: No

Text entries:
- current license: Class A CDL with T and X endorsements; original issue date 2018-08-30
- alternate phone: blank
- former last name: blank
- Other referral source: Spokane County Careers website / direct JR100708 job posting

No selection or text value was changed during the taxonomy probe.


## PCENG4-SPOKANE-059 — Application Questions staged and verified

Result: **OK**.

Fresh Workday readback confirms:
- currently employed by Spokane County: No
- under 18: No
- can submit proof of legal right to work in the U.S.: Yes
- supervising/management experience: Yes
- relatives employed by Spokane County: No
- certifications/licenses text: `Class A CDL; T and X endorsements. Original issue date: 08/30/2018.`
- alternate phone: blank
- former last name: blank
- referral source: `Spokane County Careers website / direct JR100708 job posting.`

No Save and Continue or final submit occurred during this operation.

Next:
- advance to Voluntary Disclosures;
- map controls before changing them;
- use only user-supplied voluntary EEO facts if appropriate: Male; White (Not Hispanic or Latino); veteran status No.


## PCENG4-SPOKANE-060 — Advance blocked by conditional supervision detail

Result: **Workday validation blocked navigation; still on Application Questions**.

When Save and Continue was invoked, Workday revealed a conditional required field triggered by `Do you have supervising/management experience? = Yes`:

`Please provide the number of employees you have supervised and how long you have been supervising.`

- New control: `primaryQuestionnaire--23fdc2fc18e810011d51c99eaaf50000`
- Current value: blank
- Workday error states the field is required and must have a value.
- No Voluntary Disclosures values were changed because navigation did not occur.

Source-control rule:
- Do not invent a supervision headcount or duration.
- Prior source review found no exact count/duration in the transportation/logistics resumes.
- A separate local Manager Resume may contain a supported team-size claim and must be inspected before answering.


## PCENG4-SPOKANE-060/061 — Conditional supervision detail discovered and sourced

The first attempt to advance from Application Questions did **not** reach Voluntary Disclosures. Workday exposed a conditional required text field after the applicant answered Yes to supervising/management experience:

`Please provide the number of employees you have supervised and how long you have been supervising.`

No demographic data was touched.

Source validation against the applicant's local Manager Resume found specific leadership evidence:
- Marten Transport, Jun 2019–Feb 2020: dispatched and managed 25 drivers.
- Montana Precision Products / Seacast, Aug 2016–Mar 2017: managed a 100-person workforce as part of a three-person managerial force.
- RLM Enterprises, Dec 2020–Jan 2022: led/coordinated a small workforce and oversaw daily operations.

Safe phrasing rule:
- distinguish direct management from shared/co-management;
- preserve each role's actual time period instead of implying one continuous headcount;
- do not use unsupported certification claims elsewhere in that older resume.


## PCENG4-SPOKANE-062 — Supervision detail accepted; Voluntary Disclosures reached

Result: **OK**.

Conditional supervision detail persisted and Step 3 advanced successfully to:
`current step 4 of 6 Voluntary Disclosures`.

Sourced supervision answer used:
- 25 drivers at Marten Transport, Jun 2019–Feb 2020;
- co-managed a 100-person workforce as part of a three-person managerial team at Montana Precision Products/Seacast, Aug 2016–Mar 2017;
- led/coordinated a small workforce at RLM Enterprises, Dec 2020–Jan 2022.

Voluntary Disclosures controls discovered:
- Veteran Status selector
- Gender selector
- race/ethnicity checkboxes including White and Hispanic/Latino
- Hispanic or Latino selector
- `I agree` checkbox
- Save and Continue

Known user-supplied voluntary EEO facts available for reuse:
- veteran: No
- gender: Male
- race: White
- ethnicity: Not Hispanic or Latino

Safety boundary:
- do not touch `I agree` until its surrounding legal/attestation text is mapped;
- no final submission or binding certification without explicit application-specific authorization.


## PCENG4-SPOKANE-063 — Voluntary options mapped; legal certification isolated

Exact voluntary-disclosure choices:
- Veteran Status includes `I AM NOT A VETERAN`.
- Gender includes `Male (United States of America)`.
- Hispanic or Latino selector includes Yes / No.
- Race/Ethnicity includes `White (United States of America)`.

The separate `I agree` checkbox is **not merely an EEO acknowledgment**. Its terms certify the truth/completeness of the application and attachments, acknowledge possible termination/refusal for false or incomplete statements, authorize/reference release language, and acknowledge possible post-offer medical examinations/inquiries and drug/alcohol screening.

Boundary:
- safe to stage user-supplied voluntary EEO answers;
- do not check `I agree` without explicit Spokane County application-specific authorization;
- do not final-submit without separate explicit authorization.


## PCENG4-SPOKANE-065 — Voluntary page gate audit

Operational state:
- voluntary-disclosure selections are staged and the ethnicity selector's intended choice was independently verified through selected-state inspection;
- the separate legal Terms and Conditions checkbox remains Off;
- Save and Continue is currently enabled while that checkbox is Off.

Safety decision:
- do not accept the legal certification proactively;
- attempt Save and Continue with the certification still Off;
- if Workday permits advancement, preserve the unchecked state;
- if Workday rejects advancement and explicitly requires acceptance, stop at that authorization gate rather than checking it automatically.


## PCENG4-SPOKANE-066 — Legal certification confirmed required

Result: Workday did **not** advance from Step 4 with the legal Terms and Conditions checkbox left Off.

Authoritative state:
- progress remains `current step 4 of 6 Voluntary Disclosures`;
- Workday surfaced `Errors Found` and `ErrorI agree`;
- legal `I agree` remains Off;
- no final submit occurred.

Diagnostic correction:
- the script also printed `ADVANCED_TO_SELF_IDENTIFY=True`, but that was a false positive caused by hidden Step 5 accessibility elements already present in the Workday DOM.
- Use the current-step progress marker and validation state as authoritative for navigation.

Authorization boundary:
- Spokane County requires the applicant to certify the application truth/completeness, acknowledge reference/background-check release language, and acknowledge possible post-offer medical examinations/inquiries and drug/alcohol screening before continuing.
- Do not check this box without explicit application-specific user authorization.


## Performance postmortem — why this application felt slow

Wall-clock comparison:
- Spokane County JR100708 workflow began about 14:05 PDT and reached the required legal-certification gate about 15:18 PDT: roughly 73 minutes.
- The immediately preceding Post Falls workflow began about 11:56 PDT and reached its pre-signature gate about 13:56 PDT: roughly 120 minutes. From the point the real Post Falls application opened, it still consumed about 103 minutes.

Spokane therefore completed the comparable staging work materially faster, despite using more automation operations.

Primary Spokane delay clusters:
1. Workday source selector, ops 019-031: 13 operations. UIA SelectionItem, Invoke, physical click, keyboard row activation, raw-value entry, nested promptOption and indicator targeting all failed before genuine native text-entry + Down/Enter committed the React control.
2. Targeted resume workflow, ops 042-053: 12 operations. Candidate comparison was followed by a 60-second Word COM timeout, missing python-docx/LibreOffice fallback, an invalid first Open XML package, package repair, multiple file-picker discovery failures, two PowerShell diagnostic-script bugs, then successful native-dialog upload.
3. Account/My Information setup: candidate-account creation encountered an RNG compatibility problem; My Information also hit a PowerShell helper alias collision and Workday debounce/readback quirks.
4. Application Questions, ops 056-062: prompts had to be reconstructed from ancestor context; the initial advance exposed a conditional supervision-detail requirement, which required source validation against an older manager resume before a truthful answer could be entered.
5. Voluntary Disclosures, ops 063-066: demographic options and legal terms were mapped separately; a safe attempt to advance with the legal checkbox Off confirmed Workday requires the certification.

Structural time cost:
- The workflow intentionally used map -> mutate -> fresh audit patterns rather than blind writes.
- Many actions were performed as separate relay round trips instead of batching known-safe operations.
- GitHub engineering documentation was written throughout the live application.
- These choices improved correctness and produced reusable automation knowledge, but increased perceived latency.

Optimization opportunities for the next application:
- Detect Workday early and use the proven native-keyboard strategy immediately for React search/select controls.
- Reuse the native HWND/#32770 upload path without rediscovering the file dialog.
- Reuse a validated Open XML resume-generation helper/template instead of probing Word/Python/LibreOffice.
- Cache stable applicant answers and selector semantics, while still remapping posting-specific questions.
- Batch multiple independent read-only audits and multiple already-validated safe writes into fewer relay turns.
- Keep map/mutate/audit for high-risk or ambiguous fields, but avoid redundant taxonomy probes when the control and options are already known.


## User authorization checkpoint — finish JR100708 automatically

The applicant explicitly authorized continuing this Spokane County application automatically through the remaining application flow, including the required legal certification and final submission when reached.

Operational rule:
- continue automatically through remaining pages;
- still verify page state and avoid inventing unsupported facts;
- use the current applicant profile and already supplied voluntary disclosures;
- preserve exact auditability of any new conditional question or certification encountered;
- treat this authorization as specific to Spokane County JR100708, not a blanket authorization for unrelated future applications.

Future engineering mission (after this application is finished):
- convert accumulated Workday/browser diagnostics into a reusable application engine that reads page structure, reasons over the canonical applicant profile and page requirements, and executes with substantially fewer model turns;
- optionally support a user-supplied AI API key;
- do not begin that implementation until JR100708 is completed.


## PCENG4-SPOKANE-067 — Certification AutomationId invalidated by rerender

Result: **COMMAND_FAILED before mutation**.

- The previously observed Terms and Conditions checkbox AutomationId returned zero matches.
- No checkbox was changed and no navigation occurred.
- Workday evidently regenerated or altered the accessibility identity of the certification control between audits.

Reusable rule:
- Do not persist Workday-generated AutomationIds even for apparently stable application controls when a semantic selector is available.
- Locate the legal checkbox by control type/name (`CheckBox` + `I agree`) and confirm it is contained by the `Terms and Conditions` group before toggling.


## PCENG4-SPOKANE-072 — Final Review exposed source-category misselection

Step 5 completed successfully and Workday reached `current step 6 of 6 Review`.

Final-review audit found one material inconsistency:
- `How Did You Hear About Us?` displays **Community Event**.
- The intended required category was **Other** because the applicant supplied the requisition directly and no supported evidence established a community-event source.
- The free-text referral explanation still references the Spokane County Careers website/direct posting.

Root cause:
- The earlier native-keyboard recovery cleared Workday validation but positional Down+Enter committed a valid option other than the intended semantic option.
- Validation success proves only that *some* valid option was committed; it does not prove the intended option was selected.

Reusable rule:
- For Workday search/select controls, after native keyboard commit, verify the selected token/value itself on a review/readback surface. Do not use validation clearance as the sole correctness check.
- Prefer semantic selection of the exact filtered option over positional Down+Enter when multiple suggestions can remain.

Do not submit while this mismatch remains.


## PCENG4-SPOKANE-074 — Review progress items are not navigational

Result: **COMMAND_FAILED before mutation**.

- Attempted to navigate from Review directly to completed Step 1 using the progress ListItem.
- Workday remained on `current step 6 of 6 Review`.
- No form data changed and Submit was not invoked.

Reusable rule:
- Workday's completed/current step accessibility ListItems are not reliable navigation controls.
- Use the explicit Back button to traverse to earlier steps unless a dedicated Edit control is discovered.
- Before repairing a prior value, inspect the target field's current selected-token/value representation rather than assuming its state.


## PCENG4-SPOKANE-084 — Workday source selector is hierarchical

Read-only/diagnostic result established the selector structure precisely.

Top-level categories include:
- College Career Center
- Direct Source
- Internal
- Job Board
- Job Fair
- Other
- Referral
- Social Media
- Staffing Agency
- Website

Selecting **Website** does not commit a value; it opens a child menu. Website children include:
- APWA Website
- Craigslist
- GFOA Website
- Handshake
- ICMA Website
- INSHRM Website
- NACO Website
- NAME Website
- PublicSafetyTesting.com
- **Spokane County**

The previously saved **Community Event** pill remains present while browsing a parent category, so parent navigation must not be mistaken for committing a new value.

For this application, the truthful terminal source is **Website → Spokane County**.

Reusable rule:
- Treat Workday source selectors as hierarchical taxonomy widgets.
- A top-level row may be a category rather than a terminal value.
- Confirm commitment only by observing the resulting selected pill/token or final Review value after choosing a terminal child.


## PCENG4-SPOKANE-088 — Application submitted successfully

Final run completed with status **OK**.

Pre-submit verification:
- Step 5 name: `Jack Monaghan`
- Step 5 date: `10/03/2026`
- Disability response: `I do not want to answer`
- Final Review error markers: `0`
- How Did You Hear About Us?: **Spokane County**
- Stale Community Event value: absent
- Required legal certification: **Yes**
- Obsolete free-text Other referral: absent
- Submit button: exactly one enabled match

Submission:
- `FINAL_SUBMIT_INVOKED=True`
- Workday returned visible pane/text: **Application Submitted**
- Confirmation text stated: `Congratulations! Your application has successfully been submitted to Spokane County Human Resources/Spokane County Civil Service.`
- Review-step marker disappeared.
- Submit button no longer present.

Final status: **SUBMITTED SUCCESSFULLY on 2026-10-03**.

### High-value reusable findings from final correction
1. Workday source selectors can be hierarchical taxonomies. Top-level `Website` was a category; terminal child `Spokane County` was the correct committed value.
2. A parent-category click can open children while leaving the old selected pill visible. Commitment must be proven by the terminal selected pill or final Review.
3. Editing an earlier completed step can invalidate later-step state. In this run, revisiting My Information reset the Step-4 legal certification and completely reset Step 5.
4. Therefore, after any backward edit, the engine must revalidate every subsequent step before submission rather than assuming previously completed state persists.
5. Final Review is the authoritative semantic correctness gate, not merely required-field validation.

### Follow-up engineering mission starts here
Build a job-application engine that performs a closed loop:
**perceive page → build semantic state → retrieve grounded applicant facts → reason only when needed → execute → verify mutation → advance → revalidate downstream state → final semantic audit → submit only under explicit policy authorization.**
