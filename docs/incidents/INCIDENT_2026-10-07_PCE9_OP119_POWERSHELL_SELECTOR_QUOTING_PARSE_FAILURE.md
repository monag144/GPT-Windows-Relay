# PCE9 OP119 PowerShell selector-quoting parse failure

OP119 was rejected by the PowerShell parser before execution because JavaScript selector strings embedded in PowerShell double-quoted literals were escaped with backslash syntax that PowerShell does not use.

Because parsing failed before execution, OP119 produced no source, test, live, browser, or backend side effects. OP120 verified the prior source hash before retrying with a quote-safe line-edit strategy.
