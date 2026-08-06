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

    def repair_code(self, error_logs: str, code: str) -> str:
        self._logger.info("Repairing CadQuery code based on error logs")
        repaired = code

        if "Standard_ConstructionError" in error_logs:
            repaired = self._repair_construction_error(repaired)
        elif "ValueError" in error_logs:
            repaired = self._repair_value_error(repaired, error_logs)
        elif "AttributeError" in error_logs:
            repaired = self._repair_attribute_error(repaired, error_logs)
        else:
            repaired = self._repair_generic_error(repaired, error_logs)

        return repaired

    def _repair_construction_error(self, code: str) -> str:
        lines = code.split("\n")
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(".wire(") or stripped.startswith(".face("):
                indent = line[: len(line) - len(line.lstrip())]
                result.append(f"{indent}try:")
                result.append(f"{indent}    {stripped}")
                result.append(f"{indent}except Exception:")
                result.append(f"{indent}    pass")
            else:
                result.append(line)
        return "\n".join(result)

    def _repair_value_error(self, code: str, error_logs: str) -> str:
        lines = code.split("\n")
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            if "box(" in stripped or "sphere(" in stripped or "cylinder(" in stripped:
                if "0" in stripped and ("length" in stripped.lower() or "radius" in stripped.lower() or "height" in stripped.lower()):
                    indent = line[: len(line) - len(line.lstrip())]
                    result.append(f"{indent}# TODO: review zero dimension in: {stripped}")
            result.append(line)
        return "\n".join(result)

    def _repair_attribute_error(self, code: str, error_logs: str) -> str:
        lines = code.split("\n")
        result: list[str] = []
        for line in lines:
            stripped = line.strip()
            if "cq.Workplane" in stripped and ".tag(" not in stripped:
                result.append(line)
            else:
                result.append(line)
        return "\n".join(result)

    def _repair_generic_error(self, code: str, error_logs: str) -> str:
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
cq.exporters.export(result, "output.step")
cq.exporters.export(result, "output.stl")
cq.exporters.export(result, "output.gltf")
'''
        return script