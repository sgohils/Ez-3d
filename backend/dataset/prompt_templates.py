from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Sequence

random.seed(42)

ScriptGenerator = Callable[[dict[str, float]], str]
PromptGenerator = Callable[[dict[str, float]], str]


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


@dataclass(frozen=True)
class ParamSpec:
    name: str
    min: float
    max: float
    step: float
    default: float
    kind: str = "float"


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    name: str
    description: str
    difficulty: DifficultyLevel
    params: tuple[ParamSpec, ...]
    generate_prompt: PromptGenerator
    generate_script: ScriptGenerator


def _rand_float(lo: float, hi: float, step: float) -> float:
    steps = round((hi - lo) / step)
    if steps <= 0:
        return lo
    n = random.randint(0, steps)
    return round(lo + n * step, 10)


def _sample_params(params: tuple[ParamSpec, ...]) -> dict[str, float]:
    return {p.name: _rand_float(p.min, p.max, p.step) for p in params}


def _prompt_box(params: dict[str, float]) -> str:
    l, w, h = params["length"], params["width"], params["height"]
    return f"Create a rectangular box with length {l}, width {w}, and height {h}."


def _script_box(params: dict[str, float]) -> str:
    l, w, h = params["length"], params["width"], params["height"]
    return (
        f"import cadquery as cq\n\n"
        f"length: float = {l}\n"
        f"width: float = {w}\n"
        f"height: float = {h}\n\n"
        f"result = cq.Workplane(\"XY\").box(length, width, height)\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_l_bracket(params: dict[str, float]) -> str:
    w, h, t, hd = params["width"], params["height"], params["thickness"], params["hole_diameter"]
    return f"Create an L-shaped mounting bracket with width {w}, height {h}, thickness {t}, and mounting holes of diameter {hd}."


def _script_l_bracket(params: dict[str, float]) -> str:
    w, h, t, hd = params["width"], params["height"], params["thickness"], params["hole_diameter"]
    return (
        f"import cadquery as cq\n\n"
        f"width: float = {w}\n"
        f"height: float = {h}\n"
        f"thickness: float = {t}\n"
        f"hole_diameter: float = {hd}\n\n"
        f"result = (\n"
        f"    cq.Workplane(\"XY\")\n"
        f"    .box(width, height, thickness)\n"
        f"    .faces(\">Z\")\n"
        f"    .workplane()\n"
        f"    .rect(width - 2 * thickness, height - 2 * thickness, forConstruction=True)\n"
        f"    .vertices()\n"
        f"    .hole(hole_diameter)\n"
        f")\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_flange(params: dict[str, float]) -> str:
    d, t, hd, hc = params["diameter"], params["thickness"], params["hole_diameter"], params["hole_count"]
    return f"Create a circular flange with diameter {d}, thickness {t}, {int(hc)} bolt holes of diameter {hd} arranged in a circular pattern."


def _script_flange(params: dict[str, float]) -> str:
    d, t, hd, hc = params["diameter"], params["thickness"], params["hole_diameter"], params["hole_count"]
    return (
        f"import cadquery as cq\n\n"
        f"diameter: float = {d}\n"
        f"thickness: float = {t}\n"
        f"hole_diameter: float = {hd}\n"
        f"hole_count: float = {hc}\n\n"
        f"result = cq.Workplane(\"XY\").circle(diameter / 2).extrude(thickness)\n"
        f"result = result.faces(\">Z\").workplane()\n"
        f"result = result.polygon(int(hole_count), diameter * 0.6, forConstruction=True)\n"
        f"result = result.vertices().hole(hole_diameter)\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_hollow_cylinder(params: dict[str, float]) -> str:
    od, id_, h = params["outer_diameter"], params["inner_diameter"], params["height"]
    return f"Create a hollow cylindrical pipe with outer diameter {od}, inner diameter {id_}, and height {h}."


def _script_hollow_cylinder(params: dict[str, float]) -> str:
    od, id_, h = params["outer_diameter"], params["inner_diameter"], params["height"]
    return (
        f"import cadquery as cq\n\n"
        f"outer_diameter: float = {od}\n"
        f"inner_diameter: float = {id_}\n"
        f"height: float = {h}\n\n"
        f"result = (\n"
        f"    cq.Workplane(\"XY\")\n"
        f"    .circle(outer_diameter / 2)\n"
        f"    .circle(inner_diameter / 2)\n"
        f"    .extrude(height)\n"
        f")\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_fillet_box(params: dict[str, float]) -> str:
    l, w, h, fr = params["length"], params["width"], params["height"], params["fillet_radius"]
    return f"Create a rectangular box with length {l}, width {w}, height {h}, and rounded edges with fillet radius {fr}."


def _script_fillet_box(params: dict[str, float]) -> str:
    l, w, h, fr = params["length"], params["width"], params["height"], params["fillet_radius"]
    return (
        f"import cadquery as cq\n\n"
        f"length: float = {l}\n"
        f"width: float = {w}\n"
        f"height: float = {h}\n"
        f"fillet_radius: float = {fr}\n\n"
        f"result = (\n"
        f"    cq.Workplane(\"XY\")\n"
        f"    .box(length, width, height)\n"
        f"    .edges()\n"
        f"    .fillet(fillet_radius)\n"
        f")\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_chamfer_box(params: dict[str, float]) -> str:
    l, w, h, cs = params["length"], params["width"], params["height"], params["chamfer_size"]
    return f"Create a rectangular box with length {l}, width {w}, height {h}, and chamfered edges with chamfer size {cs}."


def _script_chamfer_box(params: dict[str, float]) -> str:
    l, w, h, cs = params["length"], params["width"], params["height"], params["chamfer_size"]
    return (
        f"import cadquery as cq\n\n"
        f"length: float = {l}\n"
        f"width: float = {w}\n"
        f"height: float = {h}\n"
        f"chamfer_size: float = {cs}\n\n"
        f"result = (\n"
        f"    cq.Workplane(\"XY\")\n"
        f"    .box(length, width, height)\n"
        f"    .edges()\n"
        f"    .chamfer(chamfer_size)\n"
        f")\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_base_plate(params: dict[str, float]) -> str:
    l, w, t, hd, hcx, hcy = params["length"], params["width"], params["thickness"], params["hole_diameter"], params["hole_count_x"], params["hole_count_y"]
    return f"Create a base plate of length {l}, width {w}, thickness {t}, with a grid of {int(hcx)} by {int(hcy)} mounting holes of diameter {hd}."


def _script_base_plate(params: dict[str, float]) -> str:
    l, w, t, hd, hcx, hcy = params["length"], params["width"], params["thickness"], params["hole_diameter"], params["hole_count_x"], params["hole_count_y"]
    return (
        f"import cadquery as cq\n\n"
        f"length: float = {l}\n"
        f"width: float = {w}\n"
        f"thickness: float = {t}\n"
        f"hole_diameter: float = {hd}\n"
        f"hole_count_x: float = {hcx}\n"
        f"hole_count_y: float = {hcy}\n\n"
        f"result = cq.Workplane(\"XY\").box(length, width, thickness)\n"
        f"result = result.faces(\">Z\").workplane()\n"
        f"result = result.rarray(\n"
        f"    length / (int(hole_count_x) + 1),\n"
        f"    width / (int(hole_count_y) + 1),\n"
        f"    int(hole_count_x),\n"
        f"    int(hole_count_y),\n"
        f").hole(hole_diameter)\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_cylinder_holes(params: dict[str, float]) -> str:
    d, h, hd, hc = params["diameter"], params["height"], params["hole_diameter"], params["hole_count"]
    return f"Create a solid cylinder of diameter {d} and height {h}, with {int(hc)} radial holes of diameter {hd} around the top face."


def _script_cylinder_holes(params: dict[str, float]) -> str:
    d, h, hd, hc = params["diameter"], params["height"], params["hole_diameter"], params["hole_count"]
    return (
        f"import cadquery as cq\n\n"
        f"diameter: float = {d}\n"
        f"height: float = {h}\n"
        f"hole_diameter: float = {hd}\n"
        f"hole_count: float = {hc}\n\n"
        f"result = cq.Workplane(\"XY\").circle(diameter / 2).extrude(height)\n"
        f"result = result.faces(\">Z\").workplane()\n"
        f"result = result.polygon(int(hole_count), diameter * 0.6, forConstruction=True)\n"
        f"result = result.vertices().hole(hole_diameter)\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_bearing_housing(params: dict[str, float]) -> str:
    od, id_, h, wt, bhd = params["outer_diameter"], params["inner_diameter"], params["height"], params["wall_thickness"], params["bolt_hole_diameter"]
    return f"Create a bearing housing with outer diameter {od}, inner bore diameter {id_}, height {h}, wall thickness {wt}, and bolt holes of diameter {bhd}."


def _script_bearing_housing(params: dict[str, float]) -> str:
    od, id_, h, wt, bhd = params["outer_diameter"], params["inner_diameter"], params["height"], params["wall_thickness"], params["bolt_hole_diameter"]
    return (
        f"import cadquery as cq\n\n"
        f"outer_diameter: float = {od}\n"
        f"inner_diameter: float = {id_}\n"
        f"height: float = {h}\n"
        f"wall_thickness: float = {wt}\n"
        f"bolt_hole_diameter: float = {bhd}\n\n"
        f"result = (\n"
        f"    cq.Workplane(\"XY\")\n"
        f"    .circle(outer_diameter / 2)\n"
        f"    .circle(inner_diameter / 2)\n"
        f"    .extrude(height)\n"
        f")\n"
        f"result = result.faces(\">Z\").workplane()\n"
        f"result = result.polygon(4, outer_diameter * 0.7, forConstruction=True)\n"
        f"result = result.vertices().hole(bolt_hole_diameter)\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_pulley_wheel(params: dict[str, float]) -> str:
    od, id_, t, rt, hd, hh = params["outer_diameter"], params["inner_diameter"], params["thickness"], params["rim_thickness"], params["hub_diameter"], params["hub_height"]
    return f"Create a pulley wheel with outer diameter {od}, inner diameter {id_}, thickness {t}, rim thickness {rt}, hub diameter {hd}, and hub height {hh}."


def _script_pulley_wheel(params: dict[str, float]) -> str:
    od, id_, t, rt, hd, hh = params["outer_diameter"], params["inner_diameter"], params["thickness"], params["rim_thickness"], params["hub_diameter"], params["hub_height"]
    return (
        f"import cadquery as cq\n\n"
        f"outer_diameter: float = {od}\n"
        f"inner_diameter: float = {id_}\n"
        f"thickness: float = {t}\n"
        f"rim_thickness: float = {rt}\n"
        f"hub_diameter: float = {hd}\n"
        f"hub_height: float = {hh}\n\n"
        f"result = cq.Workplane(\"XY\").circle(outer_diameter / 2).extrude(thickness)\n"
        f"result = result.faces(\">Z\").workplane().circle(inner_diameter / 2).cutThruAll()\n"
        f"result = result.faces(\">Z\").workplane().circle(hub_diameter / 2).extrude(hub_height)\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_shaft_coupling(params: dict[str, float]) -> str:
    od, id_, ln, gd, ssd = params["outer_diameter"], params["inner_diameter"], params["length"], params["groove_depth"], params["set_screw_diameter"]
    return f"Create a shaft coupling with outer diameter {od}, inner diameter {id_}, length {ln}, groove depth {gd}, and set screw diameter {ssd}."


def _script_shaft_coupling(params: dict[str, float]) -> str:
    od, id_, ln, gd, ssd = params["outer_diameter"], params["inner_diameter"], params["length"], params["groove_depth"], params["set_screw_diameter"]
    return (
        f"import cadquery as cq\n\n"
        f"outer_diameter: float = {od}\n"
        f"inner_diameter: float = {id_}\n"
        f"length: float = {ln}\n"
        f"groove_depth: float = {gd}\n"
        f"set_screw_diameter: float = {ssd}\n\n"
        f"result = (\n"
        f"    cq.Workplane(\"XY\")\n"
        f"    .circle(outer_diameter / 2)\n"
        f"    .circle(inner_diameter / 2)\n"
        f"    .extrude(length)\n"
        f")\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


def _prompt_rod_end(params: dict[str, float]) -> str:
    bd, bl, hd, ed, et = params["body_diameter"], params["body_length"], params["hole_diameter"], params["ear_diameter"], params["ear_thickness"]
    return f"Create a rod end fitting with body diameter {bd}, body length {bl}, hole diameter {hd}, ear diameter {ed}, and ear thickness {et}."


def _script_rod_end(params: dict[str, float]) -> str:
    bd, bl, hd, ed, et = params["body_diameter"], params["body_length"], params["hole_diameter"], params["ear_diameter"], params["ear_thickness"]
    return (
        f"import cadquery as cq\n\n"
        f"body_diameter: float = {bd}\n"
        f"body_length: float = {bl}\n"
        f"hole_diameter: float = {hd}\n"
        f"ear_diameter: float = {ed}\n"
        f"ear_thickness: float = {et}\n\n"
        f"result = cq.Workplane(\"XY\").circle(body_diameter / 2).extrude(body_length)\n"
        f"result = result.faces(\">Z\").workplane().circle(ear_diameter / 2).extrude(ear_thickness)\n"
        f"result = result.faces(\">Z\").workplane().circle(hole_diameter / 2).cutThruAll()\n\n"
        'cq.exporters.export(result, "output.step")\n'
        'cq.exporters.export(result, "output.stl")\n'
        'cq.exporters.export(result, "output.gltf")\n'
    )


_BOX = PromptTemplate(
    id="box",
    name="Rectangular Box",
    description="Simple box primitive",
    difficulty=DifficultyLevel.BEGINNER,
    params=(
        ParamSpec("length", 20.0, 200.0, 1.0, 80.0),
        ParamSpec("width", 20.0, 200.0, 1.0, 60.0),
        ParamSpec("height", 5.0, 100.0, 1.0, 10.0),
    ),
    generate_prompt=_prompt_box,
    generate_script=_script_box,
)

_L_BRACKET = PromptTemplate(
    id="l_bracket",
    name="L-Shaped Bracket",
    description="L bracket with mounting holes",
    difficulty=DifficultyLevel.BEGINNER,
    params=(
        ParamSpec("width", 40.0, 200.0, 1.0, 100.0),
        ParamSpec("height", 40.0, 200.0, 1.0, 100.0),
        ParamSpec("thickness", 3.0, 20.0, 1.0, 6.0),
        ParamSpec("hole_diameter", 2.0, 15.0, 0.5, 5.0),
    ),
    generate_prompt=_prompt_l_bracket,
    generate_script=_script_l_bracket,
)

_FLANGE = PromptTemplate(
    id="flange",
    name="Circular Flange",
    description="Flange with bolt holes",
    difficulty=DifficultyLevel.INTERMEDIATE,
    params=(
        ParamSpec("diameter", 40.0, 300.0, 1.0, 120.0),
        ParamSpec("thickness", 3.0, 30.0, 1.0, 10.0),
        ParamSpec("hole_diameter", 2.0, 20.0, 0.5, 6.0),
        ParamSpec("hole_count", 3.0, 12.0, 1.0, 6.0),
    ),
    generate_prompt=_prompt_flange,
    generate_script=_script_flange,
)

_HOLLOW_CYLINDER = PromptTemplate(
    id="hollow_cylinder",
    name="Hollow Cylinder",
    description="Pipe or tube",
    difficulty=DifficultyLevel.BEGINNER,
    params=(
        ParamSpec("outer_diameter", 20.0, 200.0, 1.0, 80.0),
        ParamSpec("inner_diameter", 10.0, 180.0, 1.0, 50.0),
        ParamSpec("height", 20.0, 200.0, 1.0, 80.0),
    ),
    generate_prompt=_prompt_hollow_cylinder,
    generate_script=_script_hollow_cylinder,
)

_FILLET_BOX = PromptTemplate(
    id="fillet_box",
    name="Fillet Box",
    description="Box with rounded edges",
    difficulty=DifficultyLevel.BEGINNER,
    params=(
        ParamSpec("length", 20.0, 200.0, 1.0, 80.0),
        ParamSpec("width", 20.0, 200.0, 1.0, 60.0),
        ParamSpec("height", 5.0, 100.0, 1.0, 10.0),
        ParamSpec("fillet_radius", 1.0, 20.0, 0.5, 3.0),
    ),
    generate_prompt=_prompt_fillet_box,
    generate_script=_script_fillet_box,
)

_CHAMFER_BOX = PromptTemplate(
    id="chamfer_box",
    name="Chamfer Box",
    description="Box with chamfered edges",
    difficulty=DifficultyLevel.BEGINNER,
    params=(
        ParamSpec("length", 20.0, 200.0, 1.0, 80.0),
        ParamSpec("width", 20.0, 200.0, 1.0, 60.0),
        ParamSpec("height", 5.0, 100.0, 1.0, 10.0),
        ParamSpec("chamfer_size", 1.0, 15.0, 0.5, 2.0),
    ),
    generate_prompt=_prompt_chamfer_box,
    generate_script=_script_chamfer_box,
)

_BASE_PLATE = PromptTemplate(
    id="base_plate",
    name="Base Plate",
    description="Plate with grid of holes",
    difficulty=DifficultyLevel.INTERMEDIATE,
    params=(
        ParamSpec("length", 80.0, 400.0, 1.0, 200.0),
        ParamSpec("width", 80.0, 400.0, 1.0, 200.0),
        ParamSpec("thickness", 3.0, 20.0, 1.0, 8.0),
        ParamSpec("hole_diameter", 2.0, 15.0, 0.5, 5.0),
        ParamSpec("hole_count_x", 2.0, 8.0, 1.0, 4.0),
        ParamSpec("hole_count_y", 2.0, 8.0, 1.0, 4.0),
    ),
    generate_prompt=_prompt_base_plate,
    generate_script=_script_base_plate,
)

_CYLINDER_HOLES = PromptTemplate(
    id="cylinder_holes",
    name="Cylinder With Radial Holes",
    description="Cylinder with holes around top",
    difficulty=DifficultyLevel.INTERMEDIATE,
    params=(
        ParamSpec("diameter", 30.0, 200.0, 1.0, 80.0),
        ParamSpec("height", 10.0, 100.0, 1.0, 40.0),
        ParamSpec("hole_diameter", 2.0, 20.0, 0.5, 6.0),
        ParamSpec("hole_count", 3.0, 12.0, 1.0, 6.0),
    ),
    generate_prompt=_prompt_cylinder_holes,
    generate_script=_script_cylinder_holes,
)

_BEARING_HOUSING = PromptTemplate(
    id="bearing_housing",
    name="Bearing Housing",
    description="Housing with bore and bolt holes",
    difficulty=DifficultyLevel.EXPERT,
    params=(
        ParamSpec("outer_diameter", 40.0, 200.0, 1.0, 100.0),
        ParamSpec("inner_diameter", 20.0, 180.0, 1.0, 60.0),
        ParamSpec("height", 20.0, 120.0, 1.0, 50.0),
        ParamSpec("wall_thickness", 3.0, 20.0, 1.0, 8.0),
        ParamSpec("bolt_hole_diameter", 2.0, 15.0, 0.5, 5.0),
    ),
    generate_prompt=_prompt_bearing_housing,
    generate_script=_script_bearing_housing,
)

_PULLEY_WHEEL = PromptTemplate(
    id="pulley_wheel",
    name="Pulley Wheel",
    description="Wheel with rim and hub",
    difficulty=DifficultyLevel.EXPERT,
    params=(
        ParamSpec("outer_diameter", 40.0, 200.0, 1.0, 100.0),
        ParamSpec("inner_diameter", 20.0, 180.0, 1.0, 60.0),
        ParamSpec("thickness", 5.0, 40.0, 1.0, 15.0),
        ParamSpec("rim_thickness", 2.0, 20.0, 1.0, 8.0),
        ParamSpec("hub_diameter", 10.0, 80.0, 1.0, 30.0),
        ParamSpec("hub_height", 5.0, 40.0, 1.0, 15.0),
    ),
    generate_prompt=_prompt_pulley_wheel,
    generate_script=_script_pulley_wheel,
)

_SHAFT_COUPLING = PromptTemplate(
    id="shaft_coupling",
    name="Shaft Coupling",
    description="Cylindrical coupling",
    difficulty=DifficultyLevel.INTERMEDIATE,
    params=(
        ParamSpec("outer_diameter", 20.0, 120.0, 1.0, 60.0),
        ParamSpec("inner_diameter", 8.0, 100.0, 1.0, 40.0),
        ParamSpec("length", 20.0, 120.0, 1.0, 50.0),
        ParamSpec("groove_depth", 1.0, 10.0, 0.5, 3.0),
        ParamSpec("set_screw_diameter", 2.0, 10.0, 0.5, 3.0),
    ),
    generate_prompt=_prompt_shaft_coupling,
    generate_script=_script_shaft_coupling,
)

_ROD_END = PromptTemplate(
    id="rod_end",
    name="Rod End Fitting",
    description="Fitting with body and ear",
    difficulty=DifficultyLevel.EXPERT,
    params=(
        ParamSpec("body_diameter", 15.0, 80.0, 1.0, 40.0),
        ParamSpec("body_length", 20.0, 120.0, 1.0, 60.0),
        ParamSpec("hole_diameter", 3.0, 20.0, 0.5, 8.0),
        ParamSpec("ear_diameter", 15.0, 80.0, 1.0, 40.0),
        ParamSpec("ear_thickness", 3.0, 20.0, 1.0, 8.0),
    ),
    generate_prompt=_prompt_rod_end,
    generate_script=_script_rod_end,
)

_TEMPLATES: Sequence[PromptTemplate] = (
    _BOX,
    _L_BRACKET,
    _FLANGE,
    _HOLLOW_CYLINDER,
    _FILLET_BOX,
    _CHAMFER_BOX,
    _BASE_PLATE,
    _CYLINDER_HOLES,
    _BEARING_HOUSING,
    _PULLEY_WHEEL,
    _SHAFT_COUPLING,
    _ROD_END,
)

_BEGINNER = tuple(t for t in _TEMPLATES if t.difficulty == DifficultyLevel.BEGINNER)
_INTERMEDIATE = tuple(t for t in _TEMPLATES if t.difficulty == DifficultyLevel.INTERMEDIATE)
_EXPERT = tuple(t for t in _TEMPLATES if t.difficulty == DifficultyLevel.EXPERT)
_ALL = _TEMPLATES


def get_templates(difficulty: DifficultyLevel | None = None) -> Sequence[PromptTemplate]:
    if difficulty == DifficultyLevel.BEGINNER:
        return _BEGINNER
    if difficulty == DifficultyLevel.INTERMEDIATE:
        return _INTERMEDIATE
    if difficulty == DifficultyLevel.EXPERT:
        return _EXPERT
    return _ALL


def sample_template(difficulty: DifficultyLevel | None = None) -> PromptTemplate:
    pool = get_templates(difficulty) or _ALL
    return random.choice(pool)


def generate_entry(template: PromptTemplate | None = None, difficulty: DifficultyLevel | None = None) -> dict[str, Any]:
    tmpl = template or sample_template(difficulty)
    params = _sample_params(tmpl.params)
    return {
        "instruction": tmpl.generate_prompt(params),
        "code": tmpl.generate_script(params),
        "metadata": {
            "template_id": tmpl.id,
            "difficulty": tmpl.difficulty.value,
            "params": params,
            "param_specs": [
                {
                    "name": p.name,
                    "min": p.min,
                    "max": p.max,
                    "step": p.step,
                    "default": p.default,
                    "kind": p.kind,
                }
                for p in tmpl.params
            ],
        },
    }
