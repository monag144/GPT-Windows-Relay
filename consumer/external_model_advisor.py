"""Opt-in, read-only advisor backed by pinned OpenAI-compatible model APIs.

No Windows actions, tools, shell execution, browser navigation, or relay packet
emission is possible through this module. Do not pass private PC data to it.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from typing import Callable
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


class AdvisorError(RuntimeError):
    """A bounded, user-safe API error without credentials or provider payloads."""


@dataclass(frozen=True)
class Provider:
    key: str
    endpoint: str
    model: str
    env_key: str
    access: str


# Intentionally fixed endpoints and model identifiers: never dynamically infer a
# paid model or let model output supply a destination URL.
PROVIDERS = {
    "zai-free": Provider(
        key="zai-free",
        endpoint="https://api.z.ai/api/paas/v4/chat/completions",
        model="glm-4.7-flash",
        env_key="ZAI_API_KEY",
        access="Advertised zero-token-price model; account quotas apply",
    ),
    "nvidia-trial": Provider(
        key="nvidia-trial",
        endpoint="https://integrate.api.nvidia.com/v1/chat/completions",
        model="z-ai/glm-5.3-flash",
        env_key="NVIDIA_API_KEY",
        access="NVIDIA Developer Program evaluation endpoint; limits/terms apply",
    ),
}

SYSTEM = (
    "You are a bounded technical advisor for GPT Windows Relay. "
    "You may analyze a redacted, user-approved troubleshooting question. "
    "Return a suggestion in plain language only. Never claim to have run commands, "
    "clicked buttons, read files, or changed the Windows PC. "
    "The operator must independently review and authorize any action."
)
MAX_PROMPT_CHARS = 4000
MAX_RESPONSE_CHARS = 12000
MAX_TOKENS = 900


def build_payload(question: str, *, max_tokens: int = MAX_TOKENS) -> dict:
    if not isinstance(question, str) or not question.strip():
        raise AdvisorError("a nonempty, explicitly supplied question is required")
    if len(question) > MAX_PROMPT_CHARS:
        raise AdvisorError("question exceeds the 4000-character limit")
    if type(max_tokens) is not int or not 1 <= max_tokens <= MAX_TOKENS:
        raise AdvisorError("max_tokens exceeds the configured budget")
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "stream": False,
    }


def get_provider(key: str) -> Provider:
    try:
        return PROVIDERS[key]
    except (KeyError, TypeError):
        raise AdvisorError("unknown provider; choose an explicitly approved adapter") from None


def request_advice(
    question: str,
    *,
    provider: str = "zai-free",
    api_key: str | None = None,
    timeout: float = 20.0,
    opener: Callable | None = None,
) -> str:
    """Make one HTTPS text-only request, never retry, and return inert text.

    The caller has responsibility for consent and redaction before sending the
    question outside the device. The result is NOT executable or trusted.
    """
    cfg = get_provider(provider)
    payload = build_payload(question)
    if type(timeout) not in (int, float) or not 1 <= timeout <= 30:
        raise AdvisorError("timeout outside 1–30 second budget")
    secret = api_key if api_key is not None else os.environ.get(cfg.env_key)
    if not isinstance(secret, str) or not secret.strip():
        raise AdvisorError("provider API credential is not configured")
    payload["model"] = cfg.model
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urlrequest.Request(
        cfg.endpoint,
        data=data,
        headers={
            "Authorization": "Bearer " + secret.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    load = opener or urlrequest.urlopen
    try:
        with load(req, timeout=timeout) as response:
            # Response cap limits memory use and prevents huge transcript dumps.
            raw = response.read(65537)
        if len(raw) > 65536:
            raise AdvisorError("provider response exceeds size limit")
        parsed = json.loads(raw.decode("utf-8"))
        choices = parsed.get("choices")
        content = choices[0]["message"]["content"] if isinstance(choices, list) and choices else None
        if not isinstance(content, str) or not content.strip():
            raise AdvisorError("provider returned no usable text")
        if len(content) > MAX_RESPONSE_CHARS:
            raise AdvisorError("model answer exceeds permitted size")
        return content
    except HTTPError as exc:
        # Never print headers, provider response bodies, endpoint query params,
        # Authorization values, or user prompt content.
        if exc.code in (401, 403):
            raise AdvisorError("provider rejected credentials or access") from None
        if exc.code == 429:
            raise AdvisorError("provider rate limit reached; no automatic retry") from None
        raise AdvisorError("provider HTTP request failed") from None
    except (URLError, TimeoutError, OSError):
        raise AdvisorError("provider connection failed or timed out") from None
    except (ValueError, KeyError, TypeError, IndexError):
        raise AdvisorError("invalid provider response") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inert, optional external-model technical advisor")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), default="zai-free")
    parser.add_argument("--question", required=True, help="Short explicitly approved/redacted question")
    parser.add_argument("--live", action="store_true", help="Explicitly send question to remote API")
    args = parser.parse_args(argv)
    try:
        cfg = get_provider(args.provider)
        build_payload(args.question)
        if not args.live:
            print(json.dumps({
                "mode": "DRY_RUN_NO_NETWORK", "provider": cfg.key,
                "model": cfg.model, "endpoint": cfg.endpoint,
                "question_chars": len(args.question), "sends_pc_data": False,
                "result_can_execute_actions": False,
            }))
            return 0
        print(request_advice(args.question, provider=args.provider))
        return 0
    except AdvisorError as exc:
        print("ADVISOR_ERROR: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
