# Job Application Automation Defaults — Historical Compatibility Record — 2026-10-08T0650Z — 2026-10-08T0755Z

Full applicant data is stored locally at `%LOCALAPPDATA%\GPTWindowsRelay\job_profiles\jack_monaghan.json`. Git stores reusable automation policy, not the full PII profile.

## Confirmed defaults
- Prior employment with target employer/city/organization: default **No** unless target-specific evidence or Jack says otherwise.
- Related to a target employee: default **No** unless Jack says otherwise.
- Notification: **Email** primary; phone acceptable secondary.
- Veteran: **No**; do not claim veteran preference.
- Email copy: **Yes** when offered.
- F|Staff: **Jan 2025-Present**, may contact **Yes**.
- Knight: may contact **No**; contact/supervisor **unknown; never invent one**.
- Werner Enterprises: may contact **Yes**.
- Historical salary: leave blank unless sourced; never substitute target-job pay.
- Desired compensation: use the target posting range when supplied.
- Ten-year history: use the canonical profile, currently 18 supported employment records extending to 2012.
- Applicant-confirmed facts override conflicting resume versions.
- Never invent supervisors, pay, dates, credentials, degrees, endorsements, references, or legal attestations.
- Agreement, signature, and final submission require explicit authorization for each application.

## Education
- Northern Pacific High School — Northgate, WA — High School Diploma, 2012.
- North Seattle College — Northgate, WA — coursework/training; do not infer a degree.

## Integration
- `windows-relay/resume_profile.py`
- `windows-relay/job_application_helper.py`
- `%LOCALAPPDATA%\GPTWindowsRelay\job_profiles\jack_monaghan.json`
