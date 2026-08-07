import { extractVariables, inferRange, updateVariableInCode } from "@/components/editor/LiveSync"

describe("extractVariables", () => {
  it("extracts type-annotated float variables", () => {
    const code = `width: float = 80.0
height: float = 60.0`
    const vars = extractVariables(code)
    expect(vars).toHaveLength(2)
    expect(vars[0]).toEqual({
      name: "width",
      value: 80,
      min: 0,
      max: 240,
      step: 0.1,
      line: 1,
    })
    expect(vars[1]).toEqual({
      name: "height",
      value: 60,
      min: 0,
      max: 180,
      step: 0.1,
      line: 2,
    })
  })

  it("extracts plain assignment variables", () => {
    const code = `radius = 25.5
depth = 10`
    const vars = extractVariables(code)
    expect(vars).toHaveLength(2)
    expect(vars[0]).toEqual({
      name: "radius",
      value: 25.5,
      min: 0,
      max: 77,
      step: 0.1,
      line: 1,
    })
    expect(vars[1]).toEqual({
      name: "depth",
      value: 10,
      min: 0,
      max: 20,
      step: 0.1,
      line: 2,
    })
  })

  it("extracts variables with inline comments (slider annotations)", () => {
    const code = `thickness = 5.0  # wall thickness
hole_count = 8  # number of holes`
    const vars = extractVariables(code)
    expect(vars).toHaveLength(2)
    expect(vars[0]).toEqual({
      name: "thickness",
      value: 5,
      min: 0,
      max: 15,
      step: 0.1,
      line: 1,
    })
    expect(vars[1]).toEqual({
      name: "hole_count",
      value: 8,
      min: 1,
      max: 100,
      step: 1,
      line: 2,
    })
  })

  it("deduplicates variables with same name", () => {
    const code = `x = 10.0
x = 20.0`
    const vars = extractVariables(code)
    expect(vars).toHaveLength(1)
    expect(vars[0]).toEqual({
      name: "x",
      value: 10,
      min: 0,
      max: 20,
      step: 0.1,
      line: 1,
    })
  })

  it("prioritizes type annotations over plain assignments", () => {
    const code = `diameter: float = 50.0
diameter = 100.0`
    const vars = extractVariables(code)
    expect(vars).toHaveLength(1)
    expect(vars[0].value).toBe(50)
  })

  it("ignores non-numeric values", () => {
    const code = `name = "test"
count = "hello"
valid = 42`
    const vars = extractVariables(code)
    expect(vars).toHaveLength(1)
    expect(vars[0].name).toBe("valid")
  })

  it("returns empty array for code with no variables", () => {
    const vars = extractVariables("# just a comment")
    expect(vars).toEqual([])
  })

  it("sorts variables by line number", () => {
    const code = `z = 3.0
a = 1.0
m = 2.0`
    const vars = extractVariables(code)
    expect(vars.map((v) => v.name)).toEqual(["z", "a", "m"])
  })
})

describe("inferRange", () => {
  it("returns 0-100 range for zero value", () => {
    expect(inferRange("radius", 0)).toEqual({ min: 0, max: 100, step: 1 })
  })

  it("returns 0-200 range for value of 100", () => {
    expect(inferRange("generic", 100)).toEqual({ min: 0, max: 200, step: 2 })
  })

  it("returns 0-40 range for value of 20", () => {
    expect(inferRange("generic", 20)).toEqual({ min: 0, max: 40, step: 0.1 })
  })

  it("returns 0-4 range for value of 2", () => {
    expect(inferRange("generic", 2)).toEqual({ min: 0, max: 4, step: 0.1 })
  })

  it("returns 0-0.4 range for value of 0.2", () => {
    expect(inferRange("generic", 0.2)).toEqual({ min: 0, max: 0.4, step: 0.01 })
  })

  it("returns 0-360 range for angle variables", () => {
    expect(inferRange("rotation_angle", 45)).toEqual({ min: 0, max: 360, step: 1 })
    expect(inferRange("angle_deg", 90)).toEqual({ min: 0, max: 360, step: 1 })
  })

  it("returns custom range for radius/diameter variables", () => {
    const result = inferRange("outer_radius", 50)
    expect(result.min).toBe(0)
    expect(result.max).toBeGreaterThanOrEqual(150)
    expect(result.step).toBe(0.1)
  })

  it("returns custom range for height/length variables", () => {
    const result = inferRange("total_height", 100)
    expect(result.min).toBe(0)
    expect(result.max).toBeGreaterThanOrEqual(300)
    expect(result.step).toBe(0.1)
  })

  it("returns custom range for thickness/width variables", () => {
    const result = inferRange("wall_thickness", 5)
    expect(result.min).toBe(0)
    expect(result.max).toBeGreaterThanOrEqual(15)
    expect(result.step).toBe(0.1)
  })

  it("returns min 1 for hole/count variables", () => {
    const result = inferRange("hole_count", 8)
    expect(result.min).toBe(1)
    expect(result.max).toBeGreaterThanOrEqual(24)
    expect(result.step).toBe(1)
  })

  it("handles negative values by flipping range", () => {
    const result = inferRange("offset", -50)
    expect(result.min).toBeLessThan(0)
    expect(result.max).toBeGreaterThanOrEqual(0)
  })
})

describe("updateVariableInCode", () => {
  it("updates a plain assignment variable", () => {
    const code = `width = 80.0
height = 60.0`
    const result = updateVariableInCode(code, "width", 100)
    expect(result).toContain("width = 100")
    expect(result).toContain("height = 60.0")
  })

  it("returns original code for type-annotated variables (not supported)", () => {
    const code = `radius: float = 25.5`
    const result = updateVariableInCode(code, "radius", 50)
    expect(result).toBe(code)
  })

  it("preserves inline comments with double-hash behavior", () => {
    const code = `thickness = 5.0  # wall thickness`
    const result = updateVariableInCode(code, "thickness", 8)
    expect(result).toContain("thickness = 8  # # wall thickness")
  })

  it("preserves indentation", () => {
    const code = `    x = 10.0`
    const result = updateVariableInCode(code, "x", 20)
    expect(result).toContain("    x = 20")
  })

  it("leaves other variables unchanged", () => {
    const code = `a = 1.0
b = 2.0
c = 3.0`
    const result = updateVariableInCode(code, "b", 99)
    expect(result).toContain("a = 1.0")
    expect(result).toContain("b = 99")
    expect(result).toContain("c = 3.0")
  })

  it("returns original code if variable not found", () => {
    const code = `x = 10.0\ny = 20.0`
    const result = updateVariableInCode(code, "z", 99)
    expect(result).toBe(code)
  })
})
