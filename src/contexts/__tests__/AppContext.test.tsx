import { render, screen, waitFor, fireEvent, act } from "@testing-library/react"
import { AppProvider, useApp } from "@/contexts/AppContext"

jest.mock("@/lib/api", () => ({
  appApi: {
    generate: jest.fn(),
    recompile: jest.fn(),
  },
}))

const mockAppApi = require("@/lib/api").appApi

describe("AppContext", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("provides context values to children", () => {
    render(
      <AppProvider>
        <TestConsumer />
      </AppProvider>
    )

    expect(screen.getByTestId("context-works")).toBeInTheDocument()
  })

  it("throws error when useApp is used outside provider", () => {
    const consoleError = jest.spyOn(console, "error").mockImplementation(() => {})
    expect(() => render(<TestConsumer />)).toThrow("useApp must be used within an AppProvider")
    consoleError.mockRestore()
  })

  it("sendPrompt calls the API and updates state on success", async () => {
    mockAppApi.generate.mockResolvedValue({
      gltf_url: "http://localhost:8000/models/test.gltf",
      stl_url: "http://localhost:8000/models/test.stl",
      step_url: "http://localhost:8000/models/test.step",
      parameters: [{ name: "width", value: 100, min: 0, max: 200, step: 0.1 }],
      code: "width = 100.0",
      logs: "",
      message: "Model generated",
    })

    render(
      <AppProvider>
        <TestSendPrompt />
      </AppProvider>
    )

    await act(async () => {
      fireEvent.click(screen.getByText("Send Prompt"))
    })

    await waitFor(() => {
      expect(mockAppApi.generate).toHaveBeenCalledWith("Hello, generate a model", {})
    })

    await waitFor(() => {
      expect(screen.getByText("Model generated")).toBeInTheDocument()
    })
  })

  it("sendPrompt adds error on failure", async () => {
    mockAppApi.generate.mockRejectedValue(new Error("API Error"))

    render(
      <AppProvider>
        <TestSendPrompt />
      </AppProvider>
    )

    await act(async () => {
      fireEvent.click(screen.getByText("Send Prompt"))
    })

    await waitFor(() => {
      expect(screen.getByText("API Error")).toBeInTheDocument()
    })
  })

  it("recompile calls the API and updates state on success", async () => {
    mockAppApi.recompile.mockResolvedValue({
      gltf_url: "http://localhost:8000/models/recompiled.gltf",
      stl_url: "http://localhost:8000/models/recompiled.stl",
      step_url: "http://localhost:8000/models/recompiled.step",
      parameters: [{ name: "width", value: 150, min: 0, max: 200, step: 0.1 }],
      code: "width = 150.0",
      logs: "",
    })

    render(
      <AppProvider>
        <TestRecompile />
      </AppProvider>
    )

    await act(async () => {
      fireEvent.click(screen.getByText("Recompile"))
    })

    await waitFor(() => {
      expect(mockAppApi.recompile).toHaveBeenCalledWith({ width: 150 })
    })
  })

  it("recompile adds error on failure", async () => {
    mockAppApi.recompile.mockRejectedValue(new Error("Recompile failed"))

    render(
      <AppProvider>
        <TestRecompile />
      </AppProvider>
    )

    await act(async () => {
      fireEvent.click(screen.getByText("Recompile"))
    })

    await waitFor(() => {
      expect(screen.getByText("Recompile failed")).toBeInTheDocument()
    })
  })

  it("updateCode updates code and extracts variables", () => {
    render(
      <AppProvider>
        <TestUpdateCode />
      </AppProvider>
    )

    expect(screen.getByText("count: 0")).toBeInTheDocument()

    fireEvent.click(screen.getByText("Update Code"))

    expect(screen.getByText("count: 2")).toBeInTheDocument()
  })

  it("updateVariable updates parameter", () => {
    render(
      <AppProvider>
        <TestUpdateVariable />
      </AppProvider>
    )

    fireEvent.click(screen.getByText("Update Variable"))

    expect(screen.getByText("param: 42")).toBeInTheDocument()
  })

  it("clearErrors removes all errors", async () => {
    mockAppApi.generate.mockRejectedValue(new Error("API Error"))

    render(
      <AppProvider>
        <TestSendPrompt />
      </AppProvider>
    )

    await act(async () => {
      fireEvent.click(screen.getByText("Send Prompt"))
    })

    await waitFor(() => {
      expect(screen.getByText("API Error")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("Clear Errors"))

    expect(screen.queryByText("API Error")).not.toBeInTheDocument()
  })
})

function TestConsumer() {
  const ctx = useApp()
  return <div data-testid="context-works">context works</div>
}

function TestSendPrompt() {
  const { sendPrompt, chatHistory, errors, clearErrors } = useApp()
  return (
    <div>
      <button onClick={() => sendPrompt("Hello, generate a model")}>
        Send Prompt
      </button>
      <div data-testid="messages">
        {chatHistory.map((msg) => (
          <div key={msg.id}>
            {msg.content}
          </div>
        ))}
      </div>
      <div data-testid="errors">
        {errors.map((err, i) => (
          <div key={i}>{err}</div>
        ))}
      </div>
      {errors.length > 0 && (
        <button onClick={clearErrors}>Clear Errors</button>
      )}
    </div>
  )
}

function TestRecompile() {
  const { recompile, errors } = useApp()
  return (
    <div>
      <button onClick={() => recompile({ width: 150 })}>
        Recompile
      </button>
      <div data-testid="errors">
        {errors.map((err, i) => (
          <div key={i}>{err}</div>
        ))}
      </div>
    </div>
  )
}

function TestUpdateCode() {
  const { updateCode, variables } = useApp()
  return (
    <div>
      <span>count: {variables.length}</span>
      <button onClick={() => updateCode("x = 1.0\ny = 2.0")}>Update Code</button>
    </div>
  )
}

function TestUpdateVariable() {
  const { updateVariable, parameters } = useApp()
  return (
    <div>
      <span>param: {parameters.width ?? "none"}</span>
      <button onClick={() => updateVariable("width", 42)}>Update Variable</button>
    </div>
  )
}
