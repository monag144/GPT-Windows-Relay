# PCE10.002 ad-hoc Firefox window scanner false negative — 2026-10-07T2353Z

## Observation

PCE10.002 failed at its first identity-gate step with:

`PCE10_CHAT_WINDOW_COUNT_0`

The command used a newly embedded UI Automation top-level-window scan looking for a visible `MozillaWindowClass` with a descendant `urlbar-input`.

No repository checkout, clone, source mutation, live deployment, STOP, START, or browser lifecycle mutation occurred after that failure.

## Classification

**ENGINEERING HARNESS DEFECT / FORBIDDEN FIREFOX LIFECYCLE REDISCOVERY**

The Windows Relay already has a managed Firefox adapter that resolves the owned Firefox process tree, canonical tab strip, URL bar, ChatGPT conversation identity, and temporary add-on/debug window. PCE10.002 bypassed that established adapter and reimplemented a weaker generic desktop-window scanner.

That violated the source-of-truth instruction not to rediscover established Firefox lifecycle facts unless browser state changed or a named acceptance gate required it.

## Impact

- PCE10.002 consumed one operation without advancing source acceptance.
- No rollback is required because mutation never began.
- PCE10 identity remains unproven.
- The workspace-discovery/source-acceptance work in PCE10.002 never ran.

## Corrective rule

1. Reuse `Client/Relay/firefox_adapter.py` and `firefox_tab_adapter.ps1` for managed Firefox process/window/tab discovery.
2. Do not create another generic `AutomationElement.RootElement` Firefox-window scanner.
3. Establish the current managed ChatGPT conversation through the adapter before any sidebar/title mutation.
4. If semantic sidebar rename still needs a capability not present in the adapter, extend the canonical adapter deliberately and test it rather than embedding one-off UIA in an operation packet.
5. Resume source acceptance only after the PCE10 chat identity gate is positively verified.

Next authorized operation: PCE10.003.
