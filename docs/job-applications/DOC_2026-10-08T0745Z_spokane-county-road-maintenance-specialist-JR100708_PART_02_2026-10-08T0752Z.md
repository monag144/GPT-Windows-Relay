# Archived source fragment 2/4 — 2026-10-08T0752Z

9. Attach the best supported resume.
10. Perform a read-back audit of all populated fields.
11. Stop at the certification/signature/final-submit gate unless explicitly authorized.
12. Update this dossier with final state, intervention incidents, Workday control behavior and reusable lessons.

## Engineering-observation policy

Document all automation failures, Workday/Firefox quirks, selector/control mappings, replays, timeouts, manual interventions and recovery steps in enough detail that a later agent can resume without rediscovering them.

The goal is not merely to finish this application; the mission should expand the reusable job-application automation knowledge base.


## Execution log — 2026-10-03

### PCENG4-SPOKANE-001 — Open target and enumerate Firefox tabs

Result: **OK**.

- Opened the exact Spokane County Workday URL for JR100708.
- Firefox active window title: `Road Maintenance Specialist — Mozilla Firefox`.
- Browser reported 7 tabs.
- Relevant tabs currently visible:
  - `Road Maintenance Specialist - Spokane, WA - Indeed.com`
  - two tabs titled `Road Maintenance Specialist`, one of which is selected
  - `Logistics - Google Drive`
  - `Debugging - Runtime / this-firefox`
  - ChatGPT / engineering tabs
- No form fields, account credentials, certifications, signatures, or submission controls were changed by this operation.
- Next action: inspect the selected Workday tab read-only, capture live posting text and control inventory, and determine whether the selected tab is the posting page, an application surface, or a login/account gate.


### PCENG4-SPOKANE-002 — Read-only live Workday surface inspection

Result: **OK**.

Observed live Firefox window:
- `Road Maintenance Specialist — Mozilla Firefox`

Observed relevant visible controls on the selected Workday posting:
- `careers home` hyperlink
- `Sign In` button
- `Home` button
- `Search for Jobs` button
- `Introduce Yourself` button
- `Apply` button
- `Play video Why Work Here` button

Observed live page URL:
- `spokanecounty.wd503.myworkdayjobs.com/en-US/Spokane/job/Public-Works-Building/Road-Maintenance-Specialist_JR100708`

Observed live title:
- `Road Maintenance Specialist`

Notes:
- The selected surface is confirmed as the public posting page, not yet an application form.
- UI Automation exposed the top-level actionable controls reliably by visible name, but did not expose the deeper posting body text in the current viewport through the filtered text scan.
- No application fields or account data were changed.
- No clicks were performed in this inspection.
- Next action: invoke the visible `Apply` button, wait for Workday transition, and immediately inventory the destination surface before entering any data.


### PCENG4-SPOKANE-003 — Enter application flow

Result: **OK**.

Action performed:
- Invoked the visible `Apply` button on the public JR100708 posting.

Workday presented three application-start choices:
- `Autofill with Resume`
- `Apply Manually`
- `Use My Last Application`

No applicant data was entered.

#### Path decision

Use **Apply Manually** for this mission.

Reason:
- resume autofill may parse dates, employers, credentials, education, or contact data incorrectly;
- last-application reuse may import stale answers or answers tailored to another Spokane County requisition;
- the canonical local profile plus explicit source/provenance rules are more reliable and auditable;
- manual mode still allows automation to populate fields deterministically and record Workday field mappings.

The other paths are not inherently forbidden; they are simply not preferred when a deterministic canonical profile is available.

Next action:
- invoke `Apply Manually`;
- inventory the first application page before entering any data;
- document Workday page structure, fields, required markers and navigation controls.


### PCENG4-SPOKANE-004 — Select manual application path and inspect first page

Result: **OK**.

Action performed:
- Invoked `Apply Manually`.

Workday navigation result:
- URL changed to:
  `spokanecounty.wd503.myworkdayjobs.com/en-US/Spokane/job/Public-Works-Building/Road-Maintenance-Specialist_JR100708/apply/applyManually`

Observed surface:
- `Sign In`
- `Home`
- `Search for Jobs`
- `Introduce Yourself`
- `Back to Job Posting`
- Spokane County social/careers links

Unexpected finding:
- The first filtered UI Automation pass exposed **no application form edits, dropdowns, radios or applicant-data controls**.
- The page title remained `Road Maintenance Specialist`.
- No form data was entered.
- This is likely an intermediate Workday candidate/account surface or a state where the relevant controls are outside the current visible/accessibility subset.

Engineering consequence:
- Do **not** guess that the application form failed or that an account must be created yet.
- Perform a broader read-only accessibility scan, including offscreen interactive elements and unfiltered nonempty text, before taking another action.
- If the page proves to be an authentication gate, inventory the exact sign-in/create-account choices before entering credentials or creating anything.

No manual intervention was required.


### PCENG4-SPOKANE-005 — Broad accessibility scan; delayed Workday transition discovered

Result: **OK, but diagnostic output was polluted and truncated**.

Important successful finding:
- Active Firefox window title had changed to **`Create Account — Mozilla Firefox`**.
- The URL remained the JR100708 manual-application route:
  `.../Road-Maintenance-Specialist_JR100708/apply/applyManually`
- This establishes that Workday's manual-apply route transitioned asynchronously into a **Create Account** gate after PCENG4-SPOKANE-004 completed.

Engineering issue discovered:
- A broad Firefox UI Automation descendant scan that includes offscreen elements can expose accessibility content from **other Firefox tabs**, not only the selected Workday page.
- The scan therefore captured large amounts of hidden ChatGPT-tab content and unrelated controls.
- Relay stdout reached 37,281 characters and was truncated.
- This is a diagnostic-quality failure, not an application-state failure.
- No user intervention was required and no applicant data was changed.

### New automation rule from this incident

For Firefox page-state inspection:
1. Prefer selected-window title plus **visible/non-offscreen** controls first.
2. Keep name/text filters narrow and target-specific.
3. Never use an unrestricted all-tab/offscreen descendant text dump as a routine inspection method.
4. Treat Firefox accessibility results containing unrelated tab content as contaminated.
5. Keep relay diagnostic output bounded to avoid truncation.
6. Account for asynchronous Workday transitions by waiting/re-scanning before concluding that a page has no controls.

Current application state:
- Workday is at a **Create Account** gate.
- No credentials or applicant data have been entered yet.
- Next action: perform a compact visible-only account-gate scan and map exact email/password/create-account/sign-in controls.


### PCENG4-SPOKANE-006 — Clean visible-only Create Account scan

Result: **OK**.

Confirmed active state:
- Firefox window: `Create Account — Mozilla Firefox`
- Workday has placed the manual application behind a candidate-account gate.

Visible Workday account controls:
- `Sign In` button
- `Back to Job Posting` link
- `Email Address` edit control — AutomationId `input-4` — blank
- `Password` edit control — AutomationId `input-5` — blank/redacted by diagnostic output

Visible text:
- `Create Account`
- `Password Requirements:`

No applicant data or credentials were entered.

Engineering improvement:
- Visible-only filtering successfully avoided the cross-tab accessibility contamination seen in PCENG4-SPOKANE-005.
- Next inspection should identify the selected Firefox page's `ControlType.Document` subtree and query within that document only. If reliable, this becomes the preferred way to inspect below-the-fold/offscreen page controls without leaking accessibility content from other tabs.


### PCENG4-SPOKANE-007 — Document-scoped Workday account-form mapping

Result: **OK**.

This operation validated a better Firefox/Workday inspection method:
- exactly one visible `ControlType.Document` was found;
- document name: `Create Account`;
- querying descendants of that document exposed the complete Workday page, including below-the-fold controls, **without unrelated-tab contamination**.

#### Create Account control map

- Email Address — `input-4`
- Password — `input-5`
- Verify New Password — `input-6`
- Create Account — button
