import unittest

from backend.services.llm_pipeline import (
    extract_parameters,
    infer_range,
    substitute_parameters,
)


class TestInferRange(unittest.TestCase):
    def test_zero_value(self):
        result = infer_range("diameter", 0)
        self.assertEqual(result, {"min": 0, "max": 100, "step": 1})

    def test_large_value(self):
        result = infer_range("length", 1500)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 4500)
        self.assertEqual(result["step"], 0.1)

    def test_medium_value(self):
        result = infer_range("width", 50)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 150)
        self.assertEqual(result["step"], 0.1)

    def test_small_value(self):
        result = infer_range("thickness", 3)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 9)
        self.assertEqual(result["step"], 0.1)

    def test_tiny_value(self):
        result = infer_range("gap", 0.5)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 1.0)
        self.assertEqual(result["step"], 0.01)

    def test_very_small_value(self):
        result = infer_range("tolerance", 0.05)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 0.1)
        self.assertEqual(result["step"], 0.01)

    def test_angle_override(self):
        result = infer_range("angle", 45)
        self.assertEqual(result, {"min": 0, "max": 360, "step": 1})

    def test_radius_override(self):
        result = infer_range("radius", 10)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 30)
        self.assertEqual(result["step"], 0.1)

    def test_height_override(self):
        result = infer_range("height", 20)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 60)
        self.assertEqual(result["step"], 0.1)

    def test_width_override(self):
        result = infer_range("width", 25)
        self.assertEqual(result["min"], 0)
        self.assertEqual(result["max"], 75)
        self.assertEqual(result["step"], 0.1)

    def test_hole_count_override(self):
        result = infer_range("hole_count", 8)
        self.assertEqual(result["min"], 1)
        self.assertEqual(result["max"], 100)
        self.assertEqual(result["step"], 1)

    def test_negative_value(self):
        result = infer_range("offset", -10)
        self.assertEqual(result["min"], -20)
        self.assertEqual(result["max"], 0)
        self.assertEqual(result["step"], 0.1)


class TestExtractParameters(unittest.TestCase):
    def test_type_annotated_variables(self):
        code = """
import cadquery as cq

length: float = 80.0
width: float = 60.0

result = cq.Workplane("XY").box(length, width, 10)
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 2)
        self.assertEqual({p["name"] for p in params}, {"length", "width"})
        self.assertEqual(params[0]["value"], 80.0)
        self.assertEqual(params[1]["value"], 60.0)

    def test_plain_variables(self):
        code = """
import cadquery as cq

diameter = 25.0
thickness = 5.0

result = cq.Workplane("XY").circle(diameter / 2)
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 2)
        self.assertEqual({p["name"] for p in params}, {"diameter", "thickness"})

    def test_duplicate_names(self):
        code = """
length: float = 80.0
length = 90.0
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["name"], "length")
        self.assertEqual(params[0]["value"], 80.0)

    def test_slider_annotation_in_comment(self):
        code = """
length: float = 80.0  # [slider: 10 - 200, step: 1]
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["min"], 10)
        self.assertEqual(params[0]["max"], 200)
        self.assertEqual(params[0]["step"], 1)

    def test_slider_annotation_on_plain_var(self):
        code = """
width = 60.0  # [slider: 5 - 120, step: 5]
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["min"], 5)
        self.assertEqual(params[0]["max"], 120)
        self.assertEqual(params[0]["step"], 5)

    def test_inferred_range(self):
        code = """
length: float = 80.0
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["min"], 0)
        self.assertEqual(params[0]["max"], 240)
        self.assertEqual(params[0]["step"], 0.1)

    def test_mixed_annotations_and_plain(self):
        code = """
length: float = 80.0  # [slider: 10 - 200, step: 1]
width = 60.0
diameter: float = 25.0
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 3)
        length = next(p for p in params if p["name"] == "length")
        self.assertEqual(length["min"], 10)
        self.assertEqual(length["max"], 200)
        self.assertEqual(length["step"], 1)

        width = next(p for p in params if p["name"] == "width")
        self.assertEqual(width["min"], 0)
        self.assertEqual(width["max"], 180)
        self.assertEqual(width["step"], 0.1)

    def test_ignores_non_numeric(self):
        code = """
name = "test"
count = 5
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["name"], "count")

    def test_ignores_comments(self):
        code = """
# This is a comment
# param: old_style = 10, min = 0, max = 100, step = 1
length = 80.0
"""
        params = extract_parameters(code)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["name"], "length")


class TestSubstituteParameters(unittest.TestCase):
    def test_simple_replacement(self):
        code = "length = 80.0\nwidth = 60.0\n"
        result = substitute_parameters(code, {"length": 100.0})
        self.assertIn("length = 100.0", result)
        self.assertIn("width = 60.0", result)

    def test_type_annotated_replacement(self):
        code = "length: float = 80.0\n"
        result = substitute_parameters(code, {"length": 100.0})
        self.assertIn("length = 100.0", result)

    def test_preserves_comment(self):
        code = "length = 80.0  # [slider: 10 - 200, step: 1]\n"
        result = substitute_parameters(code, {"length": 100.0})
        self.assertIn("length = 100.0  # [slider: 10 - 200, step: 1]", result)

    def test_trailing_expression_raises(self):
        code = "width = 10.0 + 5\n"
        with self.assertRaises(ValueError) as ctx:
            substitute_parameters(code, {"width": 20.0})
        self.assertIn("trailing expression", str(ctx.exception))

    def test_unrelated_lines_unchanged(self):
        code = "import cadquery as cq\nlength = 80.0\nresult = cq.Workplane('XY')\n"
        result = substitute_parameters(code, {"length": 100.0})
        self.assertIn("import cadquery as cq", result)
        self.assertIn("result = cq.Workplane('XY')", result)


if __name__ == "__main__":
    unittest.main()
