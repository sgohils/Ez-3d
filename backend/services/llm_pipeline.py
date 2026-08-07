from __future__ import annotations

import logging
import math
import re
from typing import Any

logger = logging.getLogger(__name__)

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
                r"([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)(.*)",
                line,
            )
            if match:
                indent = line[: len(line) - len(line.lstrip())]
                rest = match.group(2)
                stripped_rest = rest.strip()
                if stripped_rest:
                    if stripped_rest.startswith("#"):
                        result_lines.append(f"{indent}{name} = {value}{rest}")
                    else:
                        raise ValueError(
                            f"Cannot substitute parameter '{name}' in line with trailing expression: {line.strip()}"
                        )
                else:
                    result_lines.append(f"{indent}{name} = {value}")
                replaced = True
                break
        if not replaced:
            result_lines.append(line)
    return "\n".join(result_lines)


class LLMPipeline:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def generate_code(self, prompt: str, parameters: dict[str, Any] | None = None) -> str:
        self._logger.info("Generating CadQuery code for prompt: %s", prompt[:100])
        code = self._build_cadquery_script(prompt, parameters or {})
        self._logger.info("Generated code length: %d characters", len(code))
        return code

    def _build_cadquery_script(self, prompt: str, parameters: dict[str, Any]) -> str:
        param_lines = []
        for name, value in parameters.items():
            param_lines.append(f"# param: {name} = {value}, min = 0.1, max = 100.0, step = 0.1")

        param_block = "\n".join(param_lines)
        script = f'''import cadquery as cq

{param_block}

# Generated from prompt: {prompt}
result = (
    cq.Workplane("XY")
    .box(10, 10, 10)
)

# Export artifacts
# STEP: OpenCASCADE STEP export (AP242 compliant by default in CadQuery >=2.4)
cq.exporters.export(result, "output.step")
# STL: binary export with configurable tolerance (injected by sandbox)
cq.exporters.export(result, "output.stl")
# GLTF: glTF 2.0 export for Three.js compatibility
cq.exporters.export(result, "output.gltf")
'''
        return script
