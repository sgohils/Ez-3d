from __future__ import annotations

import pytest

from backend.services.llm_pipeline import (
    extract_parameters,
    substitute_parameters,
    infer_range,
    intercept_oc_errors,
)


SAMPLE_CODE_PARAM_COMMENTS = """\
import cadquery as cq

# param: length = 80.0, min = 10.0, max = 200.0, step = 1.0
# param: width = 60.0, min = 10.0, max = 200.0, step = 1.0
# param: height = 10.0, min = 1.0, max = 50.0, step = 0.5

result = cq.Workplane("XY").box(length, width, height)
cq.exporters.export(result, "output.step")
"""

SAMPLE_CODE_BRACKET_PARAMS = """\
import cadquery as cq

# param: diameter: 25.0 [10.0, 50.0, 0.5]
# param: thickness: 5.0 [1.0, 20.0, 0.1]

result = cq.Workplane("XY").circle(diameter).extrude(thickness)
cq.exporters.export(result, "output.step")
"""


class TestExtractParameters:
    def test_comma_style_params(self) -> None:
        params = extract_parameters(SAMPLE_CODE_PARAM_COMMENTS)
        names = {p["name"] for p in params}
        assert "length" in names
        assert "width" in names
        assert "height" in names

    def test_bracket_style_params(self) -> None:
        params = extract_parameters(SAMPLE_CODE_BRACKET_PARAMS)
        names = {p["name"] for p in params}
        assert "diameter" in names
        assert "thickness" in names

    def test_inline_comment_min_max_step(self) -> None:
        params = extract_parameters(SAMPLE_CODE_PARAM_COMMENTS)
        length_param = next(p for p in params if p["name"] == "length")
        assert length_param["min"] == 10.0
        assert length_param["max"] == 200.0
        assert length_param["step"] == 1.0

    def test_bracket_comment_min_max_step(self) -> None:
        params = extract_parameters(SAMPLE_CODE_BRACKET_PARAMS)
        diameter_param = next(p for p in params if p["name"] == "diameter")
        assert diameter_param["min"] == 10.0
        assert diameter_param["max"] == 50.0
        assert diameter_param["step"] == 0.5

    def test_values_are_floats(self) -> None:
        params = extract_parameters(SAMPLE_CODE_PARAM_COMMENTS)
        for p in params:
            assert isinstance(p["value"], float)

    def test_returns_list_of_dicts(self) -> None:
        params = extract_parameters("x = 1.0")
        assert isinstance(params, list)
        assert all(isinstance(p, dict) for p in params)

    def test_empty_code(self) -> None:
        params = extract_parameters("")
        assert params == []


class TestSubstituteParameters:
    def test_replaces_definition_line(self) -> None:
        code = "length = 80.0\nwidth = 60.0"
        result = substitute_parameters(code, {"length": 100.0})
        assert "length = 100.0" in result
        assert "width = 60.0" in result

    def test_preserves_non_matching_lines(self) -> None:
        code = "import cadquery as cq\nlength = 80.0"
        result = substitute_parameters(code, {"length": 100.0})
        assert "import cadquery as cq" in result

    def test_preserves_usages_in_expressions(self) -> None:
        code = "length = 80.0\nresult = cq.Workplane('XY').box(length, 60, 10)"
        result = substitute_parameters(code, {"length": 100.0})
        assert "length = 100.0" in result
        assert "box(length, 60, 10)" in result

    def test_multiple_parameters(self) -> None:
        code = "a = 1.0\nb = 2.0\nc = 3.0"
        result = substitute_parameters(code, {"a": 10.0, "b": 20.0})
        assert "a = 10.0" in result
        assert "b = 20.0" in result
        assert "c = 3.0" in result

    def test_returns_string(self) -> None:
        result = substitute_parameters("x = 1.0", {"x": 2.0})
        assert isinstance(result, str)

    def test_no_match_returns_original(self) -> None:
        code = "import cadquery as cq"
        result = substitute_parameters(code, {"nonexistent": 1.0})
        assert result == code

    def test_preserves_trailing_comment(self) -> None:
        code = "length = 80.0  # default value"
        result = substitute_parameters(code, {"length": 100.0})
        assert "length = 100.0" in result
        assert "default value" in result

    def test_type_annotated_line(self) -> None:
        code = "length: float = 80.0"
        result = substitute_parameters(code, {"length": 100.0})
        assert "length = 100.0" in result


class TestInferRange:
    def test_large_value_range(self) -> None:
        result = infer_range("length", 1500.0)
        assert result["min"] >= 0
        assert result["max"] >= 3000

    def test_small_value_range(self) -> None:
        result = infer_range("thickness", 0.5)
        assert result["min"] == 0
        assert result["step"] <= 0.1

    def test_zero_value(self) -> None:
        result = infer_range("radius", 0.0)
        assert result["min"] == 0
        assert result["max"] == 100

    def test_angle_special_case(self) -> None:
        result = infer_range("angle", 45.0)
        assert result["min"] == 0
        assert result["max"] == 360

    def test_radius_special_case(self) -> None:
        result = infer_range("fillet_radius", 5.0)
        assert result["min"] == 0
        assert result["max"] >= 15

    def test_returns_dict_with_keys(self) -> None:
        result = infer_range("length", 10.0)
        assert "min" in result
        assert "max" in result
        assert "step" in result


class TestInterceptOCErrors:
    def test_fillet_radius_error(self) -> None:
        logs = "Standard_ConstructionError: Fillet radius too large"
        hints = intercept_oc_errors(logs)
        assert len(hints) > 0

    def test_brep_api_error(self) -> None:
        logs = "BRep_API_Reject: Cannot build solid"
        hints = intercept_oc_errors(logs)
        assert len(hints) > 0

    def test_no_match_returns_generic(self) -> None:
        logs = "Some random error"
        hints = intercept_oc_errors(logs)
        assert len(hints) == 1

    def test_empty_logs(self) -> None:
        hints = intercept_oc_errors("")
        assert hints == []

    def test_case_insensitive(self) -> None:
        logs = "fillet radius too large"
        hints = intercept_oc_errors(logs)
        assert len(hints) > 0
