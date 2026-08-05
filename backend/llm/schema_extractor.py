from .code_parser import ParameterDefinition, parse_parameters


def extract_schema(code: str) -> dict:
    parameters = parse_parameters(code)
    schema: dict[str, object] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    for param in parameters:
        prop: dict[str, object] = {
            "type": "number",
            "minimum": param.min,
            "maximum": param.max,
            "step": param.step,
        }
        if param.default is not None:
            prop["default"] = param.default
        schema["properties"][param.name] = prop
        schema["required"].append(param.name)

    schema["required"] = sorted(schema["required"])
    return schema