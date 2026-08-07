import { render, screen, fireEvent } from "@testing-library/react"
import { CodeDrawer } from "@/components/editor/CodeDrawer"

jest.mock("@monaco-editor/react", () => ({
  __esModule: true,
  default: function MockMonacoEditor({
    value,
    onChange,
    language,
    readOnly,
    height,
  }: {
    value: string
    onChange?: (value: string | undefined) => void
    language?: string
    readOnly?: boolean
    height?: string | number
  }) {
    return (
      <div data-testid="monaco-editor">
        <textarea
          data-testid="monaco-value"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          readOnly={readOnly}
        />
        <span data-testid="monaco-language">{language}</span>
        <span data-testid="monaco-readonly">{readOnly ? "readonly" : "editable"}</span>
      </div>
    )
  },
}))

jest.mock("@/lib/api/client", () => ({
  apiService: {
    recompile: jest.fn(),
  },
}))

describe("CodeDrawer", () => {
  const defaultCode = `width = 80.0
height = 60.0

result = cq.Workplane("XY").box(width, height)`

  it("does not render when closed", () => {
    render(<CodeDrawer isOpen={false} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} />)
    expect(screen.queryByText("Code Editor")).not.toBeInTheDocument()
  })

  it("renders when open", () => {
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} />)
    expect(screen.getByText("Code Editor")).toBeInTheDocument()
  })

  it("calls onClose when X button is clicked", () => {
    const onClose = jest.fn()
    render(<CodeDrawer isOpen={true} onClose={onClose} code={defaultCode} onCodeChange={jest.fn()} />)

    const closeButton = screen.getByLabelText("Close drawer")
    fireEvent.click(closeButton)
    expect(onClose).toHaveBeenCalled()
  })

  it("renders the editor with the code value", () => {
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} />)

    const editorValue = screen.getByTestId("monaco-value")
    expect(editorValue).toHaveValue(defaultCode)
  })

  it("shows Live Variables section when variables are detected", () => {
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} />)

    expect(screen.getByText("Live Variables")).toBeInTheDocument()
    expect(screen.getByText("width")).toBeInTheDocument()
    expect(screen.getByText("height")).toBeInTheDocument()
  })

  it("shows no variables message when no numeric variables found", () => {
    const codeWithoutVars = `import cadquery as cq
result = cq.Workplane("XY").box(10, 10)`
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={codeWithoutVars} onCodeChange={jest.fn()} />)

    expect(screen.getByText("No numeric variables detected in code")).toBeInTheDocument()
  })

  it("shows Recompile button when readOnly is false", () => {
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} readOnly={false} />)

    expect(screen.getByText("Recompile")).toBeInTheDocument()
  })

  it("does not show Recompile button when readOnly is true", () => {
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} readOnly={true} />)

    expect(screen.queryByText("Recompile")).not.toBeInTheDocument()
  })

  it("calls onVariablesExtracted on mount", () => {
    const onVariablesExtracted = jest.fn()
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} onVariablesExtracted={onVariablesExtracted} />)

    expect(onVariablesExtracted).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ name: "width" }),
        expect.objectContaining({ name: "height" }),
      ])
    )
  })

  it("shows unsaved indicator when editor content changes", () => {
    render(<CodeDrawer isOpen={true} onClose={jest.fn()} code={defaultCode} onCodeChange={jest.fn()} />)

    const editor = screen.getByTestId("monaco-value")
    fireEvent.change(editor, { target: { value: defaultCode + "\n# comment" } })

    expect(screen.getByText("unsaved")).toBeInTheDocument()
  })
})
