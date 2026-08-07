from __future__ import annotations

import logging
import math
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


TYPE_ANNOTATION_PATTERN = re.compile(
    r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(?:float|int|Decimal)\s*=\s*"
    r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(?:(#[^\n]*))?$",
    re.MULTILINE,
)

VARIABLE_PATTERN = re.compile(
    r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"
    r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(?:(#[^\n]*))?$",
    re.MULTILINE,
)

SLIDER_ANNOTATION_PATTERN = re.compile(
    r"\[\s*slider\s*:\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*-\s*"
    r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*,\s*step\s*:\s*"
    r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*\]",
    re.IGNORECASE,
)


def infer_range(name: str, value: float) -> dict[str, float]:
    abs_value = abs(value)

    if abs_value == 0:
        return {"min": 0, "max": 100, "step": 1}

    if abs_value >= 1000:
        min_val = 0
        max_val = math.ceil(abs_value * 2 / 1000) * 1000
        step = max(1, math.floor(max_val / 100))
    elif abs_value >= 100:
        min_val = 0
        max_val = math.ceil(abs_value * 2 / 100) * 100
        step = max(1, math.floor(max_val / 100))
    elif abs_value >= 10:
        min_val = 0
        max_val = math.ceil(abs_value * 2 / 10) * 10
        step = max(0.1, math.floor(max_val / 100) / 10)
    elif abs_value >= 1:
        min_val = 0
        max_val = math.ceil(abs_value * 2)
        step = 0.1
    else:
        min_val = 0
        max_val = math.ceil(abs_value * 2 * 10) / 10
        step = 0.01

    lower_name = name.lower()
    if "angle" in lower_name or "deg" in lower_name:
        min_val = 0
        max_val = 360
        step = 1
    elif "radius" in lower_name or "diameter" in lower_name:
        min_val = 0
        max_val = math.ceil(abs_value * 3)
        step = 0.1
    elif "height" in lower_name or "length" in lower_name:
        min_val = 0
        max_val = math.ceil(abs_value * 3)
        step = 0.1
    elif "thick" in lower_name or "width" in lower_name:
        min_val = 0
        max_val = math.ceil(abs_value * 3)
        step = 0.1
    elif "hole" in lower_name or "count" in lower_name:
        min_val = 1
        max_val = max(100, math.ceil(abs_value * 3))
        step = 1

    if value < 0:
        tmp = min_val
        min_val = -max_val
        max_val = -tmp

    step = float(f"{step:.10f}")

    return {"min": min_val, "max": max_val, "step": step}


def extract_parameters(code: str) -> list[dict[str, Any]]:
    parameters: list[dict[str, Any]] = []
    seen: set[str] = set()

    for pattern in (TYPE_ANNOTATION_PATTERN, VARIABLE_PATTERN):
        for match in pattern.finditer(code):
            name = match.group(1)
            if name in seen:
                continue
            value = float(match.group(2))
            comment = match.group(3)

            min_val = None
            max_val = None
            step = None

            if comment:
                slider_match = SLIDER_ANNOTATION_PATTERN.search(comment)
                if slider_match:
                    min_val = float(slider_match.group(1))
                    max_val = float(slider_match.group(2))
                    step = float(slider_match.group(3))

            if min_val is None:
                range_info = infer_range(name, value)
                min_val = range_info["min"]
                max_val = range_info["max"]
                step = range_info["step"]

            seen.add(name)
            parameters.append({
                "name": name,
                "value": value,
                "min": min_val,
                "max": max_val,
                "step": step,
            })

    return parameters


def substitute_parameters(code: str, parameters: dict[str, Any]) -> str:
    lines = code.split("\n")
    result_lines: list[str] = []
    for line in lines:
        replaced = False
        for name, value in parameters.items():
            match = re.match(
                r"^\s*" + re.escape(name) + r"\s*(?::\s*(?:float|int|Decimal)\s*)?=\s*"
                r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)",
                line,
            )
            if match:
                indent = line[: len(line) - len(line.lstrip())]
                rest = line[match.end() :].strip()
                if rest:
                    if rest.startswith("#"):
                        result_lines.append(f"{indent}{name} = {value}  {rest}")
                    else:
                        result_lines.append(f"{indent}{name} = {value}  # {rest}")
                else:
                    result_lines.append(f"{indent}{name} = {value}")
                replaced = True
                break
        if not replaced:
            result_lines.append(line)
    return "\n".join(result_lines)


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
