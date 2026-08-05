import re
from dataclasses import dataclass


PARAMETER_ANNOTATION_RE = re.compile(
    r"#\s*\[slider:\s*(?P<min>-?\d+(?:\.\d+)?)\s*-\s*(?P<max>-?\d+(?:\.\d+)?)\s*,\s*step:\s*(?P<step>-?\d+(?:\.\d+)?)\s*\]"
)

VARIABLE_ASSIGNMENT_RE = re.compile(
    r"^\s*(?P<name>[a-zA-Z_]\w*)\s*=\s*(?P<value>.+?)\s*$"
)


@dataclass
class ParameterDefinition:
    name: str
    min: float
    max: float
    step: float
    default: float | None = None


def parse_parameters(code: str) -> list[ParameterDefinition]:
    lines = code.splitlines()
    parameters: list[ParameterDefinition] = []

    for i, line in enumerate(lines):
        match = PARAMETER_ANNOTATION_RE.search(line)
        if not match:
            continue

        param_min = float(match.group("min"))
        param_max = float(match.group("max"))
        param_step = float(match.group("step"))

        var_name: str | None = None
        default_value: float | None = None

        for j in range(i + 1, min(i + 3, len(lines))):
            next_line = lines[j].strip()
            if not next_line or next_line.startswith("#"):
                continue
            var_match = VARIABLE_ASSIGNMENT_RE.match(next_line)
            if var_match and var_match.group("name") != "result":
                var_name = var_match.group("name")
                try:
                    default_value = float(var_match.group("value"))
                except (ValueError, TypeError):
                    default_value = None
                break

        if var_name is None:
            continue

        parameters.append(
            ParameterDefinition(
                name=var_name,
                min=param_min,
                max=param_max,
                step=param_step,
                default=default_value,
            )
        )

    return parameters