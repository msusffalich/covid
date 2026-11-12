"""Stateless OpenAI Responses transport; no provider SDK dependency."""
import json
import os
import urllib.error
import urllib.request


def respond(system, content, *, api_key=None, max_tokens=900, timeout=90,
            schema=None, json_schema=None, cache_key="global-pulse"):
    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OPENAI_API_KEY no configurada: análisis pendiente")
    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        "input": [{"role": "system", "content": system},
                  {"role": "user", "content": content}],
        "max_output_tokens": max_tokens, "store": False,
        "text": {"format": {"type": "json_object"}},
    }
    if payload["model"].startswith("gpt-4.1"):
        payload["prompt_cache_key"] = cache_key
    if json_schema:
        payload["text"]["format"] = {"type": "json_schema", "name": "resultado",
                                      "strict": True, "schema": json_schema}
    if schema:
        # Existing Nexo schemas include open analysis objects. Non-strict function
        # schemas preserve that contract without inventing a narrower schema.
        payload.pop("text")
        payload["tools"] = [{"type": "function", "name": "entregar_resultado",
                             "description": "Devuelve los datos estructurados solicitados.",
                             "parameters": schema, "strict": False}]
        payload["tool_choice"] = {"type": "function", "name": "entregar_resultado"}
        payload["parallel_tool_calls"] = False
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Never include request headers or credentials in logs.
        try:
            detail = json.loads(error.read()).get("error", {})
            code = detail.get("code") or "api_error"
            message = str(detail.get("message", "")).replace(key, "[redacted]")[:400]
        except (ValueError, AttributeError):
            code = "api_error"
            message = ""
        raise RuntimeError(f"OpenAI HTTP {error.code}: {code} {message}".strip()) from None
    if result.get("status") != "completed":
        raise ValueError("OpenAI respuesta incompleta o fallida: " + str(result.get("status")))
    for item in result.get("output", []):
        if schema and item.get("type") == "function_call" and item.get("name") == "entregar_resultado":
            value = json.loads(item["arguments"])
            if not isinstance(value, dict):
                raise ValueError("OpenAI no devolvió un objeto JSON")
            return value
    text = "".join(block.get("text", "") for item in result.get("output", [])
                   if item.get("type") == "message" for block in item.get("content", [])
                   if block.get("type") == "output_text")
    if not text:
        raise ValueError("OpenAI no devolvió contenido utilizable")
    if schema:
        raise ValueError("OpenAI no devolvió la función requerida")
    return text
