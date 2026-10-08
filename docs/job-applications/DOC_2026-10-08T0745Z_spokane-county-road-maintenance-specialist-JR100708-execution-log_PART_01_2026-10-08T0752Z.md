# Archived source fragment 1/6 — 2026-10-08T0752Z

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
