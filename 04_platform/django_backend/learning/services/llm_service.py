"""
Lightweight LLM service abstraction.

Backends:
  - disabled / none: raises RuntimeError
  - mock: deterministic JSON for local dev
  - anthropic: Claude via the Anthropic SDK (uses ANTHROPIC_API_KEY)
  - openai_compatible: any OpenAI-style /v1/chat/completions (OpenAI, HF TGI endpoints, etc.)
  - huggingface: Hugging Face Inference Providers via huggingface_hub.InferenceClient
"""
import json
from urllib import request as urllib_request

from django.conf import settings

_SYSTEM_PROMPT = "You are a concise GCSE tutor assistant."


def generate(prompt, max_tokens=700, temperature=0.2):
    """
    Generate text with configured LLM backend.
    Returns plain text response.
    """
    backend = (getattr(settings, "LLM_BACKEND", "disabled") or "disabled").lower()
    if backend in ("disabled", "none"):
        raise RuntimeError("LLM backend is disabled")

    if backend == "mock":
        return (
            '[{"question_text":"What is 2 + 2?","correct_answer":"4",'
            '"explanation":"Basic addition.","question_type":"short_answer",'
            '"difficulty_level":1}]'
        )

    if backend == "anthropic":
        return _generate_anthropic(prompt, max_tokens)

    if backend == "openai_compatible":
        return _generate_openai_compatible(prompt, max_tokens, temperature)

    if backend == "huggingface":
        return _generate_huggingface(prompt, max_tokens, temperature)

    raise RuntimeError(f"Unsupported LLM backend: {backend}")


DEFAULT_ANTHROPIC_MODEL = "claude-opus-5-5"


def _generate_anthropic(prompt, max_tokens):
    """
    Claude via the official Anthropic SDK.
    LLM_MODEL is used when it names a Claude model; otherwise the default.
    Temperature is not sent: current Claude models reject sampling params.
    Effort is low because these are short, latency-sensitive replies.
    """
    import anthropic

    api_key = (
        getattr(settings, "ANTHROPIC_API_KEY", "")
        or getattr(settings, "LLM_API_KEY", "")
        or ""
    ).strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = (getattr(settings, "LLM_MODEL", "") or "").strip()
    if not model.startswith("claude-"):
        model = DEFAULT_ANTHROPIC_MODEL

    client = anthropic.Anthropic(api_key=api_key, timeout=20.0, max_retries=1)
    response = client.messages.create(
        model=model,
        max_tokens=max(int(max_tokens), 1024),
        system=_SYSTEM_PROMPT,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined the request")
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        raise RuntimeError(f"Empty Claude response (stop_reason={response.stop_reason})")
    return text


def _hf_token():
    return (
        getattr(settings, "HF_TOKEN", "")
        or getattr(settings, "LLM_API_KEY", "")
        or ""
    ).strip()


def _hf_model():
    return (
        getattr(settings, "HF_MODEL", "")
        or getattr(settings, "LLM_MODEL", "")
        or ""
    ).strip()


def _generate_openai_compatible(prompt, max_tokens, temperature):
    base_url = getattr(settings, "LLM_BASE_URL", "").rstrip("/")
    model = getattr(settings, "LLM_MODEL", "")
    api_key = getattr(settings, "LLM_API_KEY", "")
    if not base_url or not model or not api_key:
        raise RuntimeError("LLM configuration incomplete for openai_compatible backend")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib_request.Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=45) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def _generate_huggingface(prompt, max_tokens, temperature):
    token = _hf_token()
    model = _hf_model()
    if not token or not model:
        raise RuntimeError(
            "Hugging Face LLM configuration incomplete: set HF_TOKEN (or LLM_API_KEY) "
            "and HF_MODEL (or LLM_MODEL)"
        )

    try:
        from huggingface_hub import InferenceClient
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is required for LLM_BACKEND=huggingface. "
            "Install with: pip install huggingface_hub"
        ) from exc

    provider = (getattr(settings, "HF_PROVIDER", "") or "").strip() or None
    client_kwargs = {"model": model, "token": token}
    if provider:
        client_kwargs["provider"] = provider

    client = InferenceClient(**client_kwargs)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if isinstance(response, dict):
            content = response["choices"][0]["message"]["content"]
        else:
            choice = response.choices[0]
            msg = choice.message
            if isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = getattr(msg, "content", "") or ""
        if content:
            return content
    except Exception:
        pass

    # Models without a chat template: plain text generation.
    combined = f"{_SYSTEM_PROMPT}\n\nUser: {prompt}\n\nAssistant:"
    return client.text_generation(
        combined,
        max_new_tokens=max_tokens,
        temperature=temperature,
        return_full_text=False,
    )
