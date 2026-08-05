from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


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
step_path = "/tmp/output.step"
stl_path = "/tmp/output.stl"
gltf_path = "/tmp/output.gltf"

cq.exporters.export(result, step_path)
cq.exporters.export(result, stl_path)
cq.exporters.export(result, gltf_path)
'''
        return script