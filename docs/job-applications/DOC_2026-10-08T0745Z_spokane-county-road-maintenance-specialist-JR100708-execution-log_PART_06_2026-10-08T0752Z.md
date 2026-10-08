# Archived source fragment 6/6 — 2026-10-08T0752Z

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
