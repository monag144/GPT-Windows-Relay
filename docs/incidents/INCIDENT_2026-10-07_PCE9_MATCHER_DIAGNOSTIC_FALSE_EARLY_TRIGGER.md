# PCE9 matcher diagnostic false-early-trigger incident

OP103 showed the OP100 diagnostic could emit before the tracked result was actually returned. It independently tested body-wide packet-ID visibility and body-wide GPT_WINDOWS_RESULT visibility, so an assistant action containing the packet ID plus an older result elsewhere in the conversation satisfied the trigger. Evidence: DIAGNOSTIC_AFTER_SEND_CLICK=False, candidate_count=0, and no local carrier. The resulting PACKET_VISIBLE_BUT_OUTSIDE_RESULT_SELECTOR classification was therefore not accepted as functional evidence.

OP105 repairs diagnostics only: the nearest protocol opener before the tracked packet ID must be GPT_WINDOWS_RESULT rather than GPT_WINDOWS_ACTION. Functional result matching, role rejection, action execution, and dedupe are unchanged.
