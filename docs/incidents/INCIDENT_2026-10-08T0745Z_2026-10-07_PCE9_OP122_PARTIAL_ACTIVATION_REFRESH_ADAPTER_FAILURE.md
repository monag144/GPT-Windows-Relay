# PCE9 OP122 partial activation / Firefox refresh-adapter failure — 2026-10-08T0745Z

OP122 successfully reloaded the existing GPT One-Click Go Relay addon exactly once, then failed before refreshing the ChatGPT tab because firefox_tab_adapter.ps1 reported FIREFOX_CHROME_RELOAD_BUTTON_COUNT_0. The complete OP122 operation must not be replayed because the addon reload is a known side effect that already occurred.

OP123 performs read-only runtime, event, UIAutomation, and adapter-path inspection to determine whether the repaired content runtime reconnected anyway or whether a narrowly targeted alternative tab-refresh mechanism is required.
