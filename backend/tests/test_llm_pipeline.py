from __future__ import annotations

import pytest
from backend.services.llm_pipeline import extract_parameters, substitute_parameters, LLMPipeline


class TestExtractParameters:
    def test_extract_parameters_format_one(self):
        code = """
# param: thickness = 2.0, min = 0.5, max = 10.0, step = 0.5
result = cq.Workplane("XY").box(10, 10, 10)
"""
        params = extract_parameters(code)
        assert len(params) == 1
        assert params[0]["name"] == "thickness"
        assert params[0]["value"] == 2.0
        assert params[0]["min"] == 0.5
        assert params[0]["max"] == 10.0
        assert params[0]["step"] == 0.5

    def test_extract_parameters_format_two(self):
        code = """
# param: width: 5.0 [1.0, 20.0, 1.0]
result = cq.Workplane("XY").box(10, 10, 10)
"""
        params = extract_parameters(code)
        assert len(params) == 1
        assert params[0]["name"] == "width"
        assert params[0]["value"] == 5.0
        assert params[0]["min"] == 1.0
        assert params[0]["max"] == 20.0
        assert params[0]["step"] == 1.0

    def test_extract_parameters_multiple(self):
        code = """
# param: length = 10.0, min = 1.0, max = 50.0, step = 1.0
# param: height: 3.0 [0.5, 15.0, 0.5]
"""
        params = extract_parameters(code)
        assert len(params) == 2

    def test_extract_parameters_none(self):
        code = "result = cq.Workplane('XY').box(10, 10, 10)"
        params = extract_parameters(code)
        assert params == []


class TestSubstituteParameters:
    def test_substitute_simple(self):
        code = "x = 10\ny = x + 5"
        result = substitute_parameters(code, {"x": "20"})
        assert "x = 20" in result
        assert "y = x + 5" not in result

    def test_substitute_word_boundary(self):
        code = "xy = 10\nx = xy"
        result = substitute_parameters(code, {"x": "5"})
        assert "xy = 10" in result
        assert "x = 5" in result

    def test_substitute_empty(self):
        code = "result = cq.Workplane('XY').box(10, 10, 10)"
        result = substitute_parameters(code, {})
        assert result == code


class TestLLMPipeline:
    def test_generate_code_returns_string(self):
        pipeline = LLMPipeline()
        code = pipeline.generate_code("Make a box")
        assert isinstance(code, str)
        assert "cadquery" in code.lower() or "import cadquery" in code

    def test_build_cadquery_script_structure(self):
        pipeline = LLMPipeline()
        script = pipeline._build_cadquery_script("test prompt", {})
        assert "import cadquery as cq" in script
        assert "result =" in script
        assert "output.step" in script

    def test_build_cadquery_script_with_parameters(self):
        pipeline = LLMPipeline()
        script = pipeline._build_cadquery_script("test prompt", {"width": 10.0})
        assert "# param: width = 10.0" in script
