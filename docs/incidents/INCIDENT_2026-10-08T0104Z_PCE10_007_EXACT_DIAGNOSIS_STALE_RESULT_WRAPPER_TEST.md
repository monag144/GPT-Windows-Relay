# PCE10.007 exact diagnosis — stale result-wrapper compatibility test

## Diagnostic result

PCE10.008 reran the complete Windows unittest suite to a dedicated diagnostic log and confirmed the PCE10.007 source-acceptance block was a single test:

`test_generic_current_turn_wrappers_are_supported` in `windows-relay/tests/test_result_turn_recognition.py`.

## Conflict

That legacy test requires generic current-turn support but also asserts that the result selector must *not* contain:

- `article[data-testid^="conversation-turn-"]`;
- `section[data-testid^="conversation-turn-"]`.

The newer regression `test_result_turn_div_wrapper_pce9.py` requires article, section, and div conversation-turn wrappers because the broader selector was introduced from live PCE9 result-confirmation evidence.

Current production source still preserves generic support:

- `USER_SELECTOR` contains `[data-turn="user"]`;
- assistant selection contains `article[data-turn="assistant"]`.

Therefore the production selector is internally consistent and the old negative assertion is stale.

## Classification

**STALE LEGACY TEST EXPECTATION**

This is not a production regression.

## Corrective change

Update only `test_result_turn_recognition.py` so it verifies both:

1. generic current `data-turn` compatibility remains present;
2. the live-proven article/section/div result-wrapper fallbacks remain present.

Production source is unchanged.

## Acceptance

Run the repaired test, the complete Windows suite, and the complete consumer suite. No live promotion until all are green.
