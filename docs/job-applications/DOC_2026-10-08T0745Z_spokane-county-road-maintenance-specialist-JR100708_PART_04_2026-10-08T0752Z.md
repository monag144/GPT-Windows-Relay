# Archived source fragment 4/4 — 2026-10-08T0752Z

- City must be treated as **unknown until audited**; a failed immediate readback does not prove whether Workday left it blank, normalized it, or entered an autocomplete/transient state.
- Postal code and phone number were not reached.
- Source, State, Phone Device Type and Country Phone Code were untouched.
- Save and Continue was not invoked.

Engineering implication:
- Some Workday address fields may be autocomplete-backed and cannot be treated as plain edit boxes even when UI Automation exposes `ValuePattern`.
- Before retrying, audit the current City value and any active suggestion/list controls.
- Prefer the existing UIA text-entry helper / keyboard-driven entry path for fields whose direct value setter does not persist, and verify post-entry state after Workday debounce.


### PCENG4-SPOKANE-016 — City write audit; delayed Workday persistence confirmed

Result: **OK**.

Current verified My Information state:
- First Name = Jack
- Last Name = Monaghan
- Previously employed by Spokane County = **No**
- Address Line 1 = canonical current street address
- City = **Liberty Lake**
- State = unselected
- Postal Code = blank
- Phone Device Type = unselected
- Country Phone Code = blank
- Phone Number = blank

Important engineering finding:
- The City write from PCENG4-SPOKANE-015 **did persist**, despite the immediate readback check reporting failure.
- Workday therefore has delayed/debounced model propagation for at least some edit fields.
- A short immediate equality check (80 ms) is not reliable enough to determine write success on Workday.

Reusable timing rule:
- After writing a Workday text field, do not treat an immediate readback mismatch as definitive failure.
- Allow a longer debounce interval and/or perform a fresh document-tree audit before retrying.
- Avoid duplicate writes caused by false-negative immediate readback.
- Maintain exact mutation boundaries from stdout, but verify ambiguous fields in a fresh read-only operation before concluding they failed.

Next:
- map the source selector, State selector and Phone Device Type selector without committing a choice;
- then complete remaining My Information fields and perform a full readback before Save and Continue.


### PCENG4-SPOKANE-017 — My Information selector options mapped

Result: **OK**.

Selector findings:

**How Did You Hear About Us?**
- Options exposed:
  - College Career Center
  - Direct Source
  - Internal
  - Job Board
  - Job Fair
  - Other
  - Referral
  - Social Media
  - Staffing Agency
- No source is currently selected.
- The available evidence does not establish how the applicant originally discovered JR100708, so do not invent a source. Leave this field blank unless Workday later proves it required or the applicant supplies the answer.

**State**
- Standard U.S. state/territory selector.
- `Washington` is an available enabled option.
- Select **Washington** for the canonical Liberty Lake address.

**Phone Device Type**
- Options: `Landline`, `Mobile`.
- Select **Mobile** for the canonical applicant phone.

**Phone country code**
- Workday exposes `United States of America (+1)`; use this for the canonical U.S. phone number.

No selector value was committed during this operation.

Engineering note:
- Workday selector controls can expose options as `ControlType.ListItem` after Expand/Invoke.
- Selector mapping should be performed separately from selection when factual provenance is uncertain; optional fields should remain blank rather than receive guessed taxonomy values.
