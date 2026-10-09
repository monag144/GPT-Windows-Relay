# Optional external-model advisor — 2026-10-09

This is an opt-in, read-only planning and troubleshooting assistant scaffold. It is not a replacement Windows Relay controller and cannot itself click, run shell commands, alter files, create relay packets or control the desktop. Source: consumer/external_model_advisor.py.

## Providers and user consent

* zai-free: Z.ai model glm-4.7-flash, endpoint https://api.z.ai/api/paas/v4/chat/completions, environment key ZAI_API_KEY. Public pricing previously listed this text model at zero token cost; current limits/availability require checking in the account.
* nvidia-trial: NVIDIA catalog model z-ai/glm-5.3-flash, endpoint https://integrate.api.nvidia.com/v1/chat/completions, environment key NVIDIA_API_KEY. The NVIDIA Developer Program offers free hosted developer evaluation access, not guaranteed unlimited production usage. Confirm developer program terms and quotas.

Official reference URLs:
https://docs.api.nvidia.com/nim/reference/z-ai-glm-5-3-flash-infer
https://docs.api.nvidia.com/nim/docs/product
https://docs.z.ai/guides/capabilities/mcp-call
https://docs.z.ai/guides/overview/pricing

### Usage

Dry run (default; no network and no credential required):

    python consumer/external_model_advisor.py --provider zai-free --question "Explain how to verify a GUI click."

Live mode (one provider POST only, requires a credential already supplied securely in the environment):

    python consumer/external_model_advisor.py --provider zai-free --live --question "Why can Firefox's title remain unchanged after SPA navigation?"

Use --provider nvidia-trial for the other endpoint. Never put actual API keys into chat, shell arguments, Git files or screenshots. The --live flag transmits exactly the supplied question to an external provider. Do not pass personal documents, chat history, credentials, browser tokens, or unredacted screenshots without a separate informed decision.

### Explicit safeguards

* Default dry-run, no network access; live calls must be explicitly opted into.
* Pin two fixed provider endpoints and model identifiers. No paid fallback. No tool/function calling and no external model output is executable.
* Limits: question <= 4000 characters; output request <= 900 tokens; 30-second max timeout; 64 KiB response; 12000-char text response.
* No automatic retries; rate-limit (HTTP 429) fails closed and reports safely.
* API secrets read from process environment; no secrets or response bodies in error logs.
* Any future bridge into actual Windows actions must be designed, separately tested and governed with explicit approval, exact-once semantics and rollback.

### Codex escalation after repeated failure

If five consecutive issued PCE ordinals target the same unresolved error signature, escalate to the installed Codex CLI with GPT-5.6 Terra at medium reasoning rather than repeating the same local approach. Example:

    codex --model gpt-5.6-terra -c 'model_reasoning_effort="medium"'

Check local CLI availability and actual model support before using it. Preserve rollback, audit provenance and existing governance. Sandbox diagnostics where possible; never automatically promote Codex output to running Windows relay without tests. Record model, command and outcome in the PCE operation log.

### Tests and limitations

Seven isolated Python unittest cases passed in the assistant test workspace. Their exact corresponding source and test Git blobs are committed to this branch. No provider key enrollment, no live remote API call, no Windows installation and no in-relay integration have been performed or claimed. This scaffold is intentionally independent of the existing live relay. No GitHub Actions credits consumed.
