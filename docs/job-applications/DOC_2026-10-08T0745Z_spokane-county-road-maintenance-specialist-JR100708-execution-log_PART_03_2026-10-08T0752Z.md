# Archived source fragment 3/6 — 2026-10-08T0752Z

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
