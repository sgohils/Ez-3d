from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

LLM_API_URL = os.environ.get("LLM_API_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = """You are a CadQuery code generation assistant. Generate valid, parametric CadQuery Python code that can be executed to produce a 3D model.

Rules:
- Output ONLY the Python code, no explanations, no markdown fences
- Use `import cadquery as cq`
- Define parametric variables with type annotations and default values, e.g. `length: float = 80.0`
- Build the geometry using `cq.Workplane("XY")`
- Export to STEP, STL, and GLTF using `cq.exporters.export(result, "output.step")`, etc.
- Do NOT use any functions that require user input or external files
- Keep the code deterministic and self-contained
- Do NOT include think blocks or reasoning in the output

Example template:
```python
import cadquery as cq

length: float = 80.0
width: float = 60.0
height: float = 10.0

result = cq.Workplane("XY").box(length, width, height)

cq.exporters.export(result, "output.step")
cq.exporters.export(result, "output.stl")
cq.exporters.export(result, "output.gltf")
```
"""


def extract_parameters(code: str) -> list[dict[str, Any]]:
    param_patterns = [
        r"(?:^|\n)\s*#\s*param:\s*(\w+)\s*=\s*([\d.]+)\s*,\s*min\s*=\s*([\d.]+)\s*,\s*max\s*=\s*([\d.]+)\s*,\s*step\s*=\s*([\d.]+)",
        r"(?:^|\n)\s*#\s*param:\s*(\w+):\s*([\d.]+)\s*\[([\d.]+),?\s*([\d.]+),?\s*([\d.]+)\]",
    ]
    parameters: list[dict[str, Any]] = []
    for pattern in param_patterns:
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            value = float(match.group(2))
            min_val = float(match.group(3))
            max_val = float(match.group(4))
            step = float(match.group(5))
            parameters.append({
                "name": name,
                "value": value,
                "min": min_val,
                "max": max_val,
                "step": step,
            })
    return parameters


def substitute_parameters(code: str, parameters: dict[str, Any]) -> str:
    result = code
    for name, value in parameters.items():
        result = re.sub(r'\b' + re.escape(name) + r'\b', str(value), result)
    return result


def _extract_code_block(response_text: str) -> str:
    text = response_text.strip()

    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)

    fence_pattern = re.compile(r'```(?:python)?\s*\n?(.*?)```', re.DOTALL | re.IGNORECASE)
    fence_matches = fence_pattern.findall(text)
    if fence_matches:
        return fence_matches[0].strip()

    return text.strip()


class LLMPipeline:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def generate_code(self, prompt: str, parameters: dict[str, Any] | None = None) -> str:
        self._logger.info("Generating CadQuery code for prompt: %s", prompt[:100])
        code = self._call_llm(prompt, parameters or {})
        self._logger.info("Generated code length: %d characters", len(code))
        return code

    def _call_llm(self, prompt: str, parameters: dict[str, Any]) -> str:
        if not LLM_API_URL:
            raise RuntimeError("LLM_API_URL is not configured")

        user_message = prompt
        if parameters:
            param_descriptions = []
            for key, value in parameters.items():
                param_descriptions.append(f"- {key}: {value}")
            user_message += "\n\nUse these parameter values:\n" + "\n".join(param_descriptions)

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
        }

        headers = {
            "Content-Type": "application/json",
        }
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"

        timeout = httpx.Timeout(60.0, connect=10.0)

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{LLM_API_URL.rstrip('/')}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"LLM API request timed out: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"LLM API returned status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"LLM API request failed: {exc}") from exc

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected LLM response format: {exc}") from exc

        code = _extract_code_block(content)
        if not code:
            raise RuntimeError("LLM returned empty code response")

        return code
