# Archived source fragment 4/6 — 2026-10-08T0752Z

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

