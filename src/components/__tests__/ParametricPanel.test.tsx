import { render, screen, fireEvent } from "@testing-library/react"
import { ParametricPanel } from "@/components/controls/ParametricPanel"
import type { CodeVariable } from "@/components/editor/LiveSync"
import { AppContext } from "@/contexts/AppContext"

const mockVariables: CodeVariable[] = [
  { name: "width", value: 80, min: 0, max: 200, step: 0.1, line: 1 },
  { name: "height", value: 60, min: 0, max: 200, step: 0.1, line: 2 },
]

describe("ParametricPanel", () => {
  it("renders empty state when no variables", () => {
    render(
      <AppContext.Provider
        value={{
          variables: [],
          parameters: {},
          recompile: jest.fn(),
          isRecompiling: false,
        } as any}
      >
        <ParametricPanel />
      </AppContext.Provider>
    )
    expect(screen.getByText("No parameters available")).toBeInTheDocument()
    expect(screen.getByText("Generate a model to see parametric controls")).toBeInTheDocument()
  })

  it("renders sliders for each variable", () => {
    render(
      <AppContext.Provider
        value={{
          variables: mockVariables,
          parameters: {},
          recompile: jest.fn(),
          isRecompiling: false,
        } as any}
      >
        <ParametricPanel />
      </AppContext.Provider>
    )

    expect(screen.getByText("width")).toBeInTheDocument()
    expect(screen.getByText("height")).toBeInTheDocument()
    expect(screen.getByText("80.00")).toBeInTheDocument()
    expect(screen.getByText("60.00")).toBeInTheDocument()
  })

  it("calls recompile on slider mouse up", () => {
    const recompile = jest.fn()
    render(
      <AppContext.Provider
        value={{
          variables: mockVariables,
          parameters: {},
          recompile,
          isRecompiling: false,
        } as any}
      >
        <ParametricPanel />
      </AppContext.Provider>
    )

    const slider = screen.getAllByRole("slider")[0]
    fireEvent.change(slider, { target: { value: "100" } })
    fireEvent.mouseUp(slider)

    expect(recompile).toHaveBeenCalledWith(
      expect.objectContaining({ width: 100 })
    )
  })

  it("calls recompile on slider touch end", () => {
    const recompile = jest.fn()
    render(
      <AppContext.Provider
        value={{
          variables: mockVariables,
          parameters: {},
          recompile,
          isRecompiling: false,
        } as any}
      >
        <ParametricPanel />
      </AppContext.Provider>
    )

    const slider = screen.getAllByRole("slider")[0]
    fireEvent.change(slider, { target: { value: "100" } })
    fireEvent.touchEnd(slider)

    expect(recompile).toHaveBeenCalledWith(
      expect.objectContaining({ width: 100 })
    )
  })

  it("shows recompiling spinner when isRecompiling is true", () => {
    render(
      <AppContext.Provider
        value={{
          variables: mockVariables,
          parameters: {},
          recompile: jest.fn(),
          isRecompiling: true,
        } as any}
      >
        <ParametricPanel />
      </AppContext.Provider>
    )

    expect(screen.getByText("Parameters")).toBeInTheDocument()
  })
})
