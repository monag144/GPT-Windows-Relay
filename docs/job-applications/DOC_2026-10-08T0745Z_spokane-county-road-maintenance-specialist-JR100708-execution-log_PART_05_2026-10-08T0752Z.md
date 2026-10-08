# Archived source fragment 5/6 — 2026-10-08T0752Z

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
