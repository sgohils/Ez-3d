import { render, screen, fireEvent, waitFor, act } from "@testing-library/react"
import { ChatSidebar } from "@/components/chat/ChatSidebar"

describe("ChatSidebar", () => {
  it("renders the chat header", () => {
    render(<ChatSidebar />)
    expect(screen.getByRole("heading", { name: "Chat" })).toBeInTheDocument()
  })

  it("renders prompt presets when dropdown is opened", () => {
    render(<ChatSidebar />)
    const presetsButton = screen.getByRole("button", { name: "Toggle prompt presets" })
    fireEvent.click(presetsButton)
    expect(screen.getByText("Prompt Presets")).toBeInTheDocument()
    expect(screen.getByText("Enclosure")).toBeInTheDocument()
    expect(screen.getByText("Mounting Bracket")).toBeInTheDocument()
    expect(screen.getByText("Spur Gear")).toBeInTheDocument()
    expect(screen.getByText("Bearing Housing")).toBeInTheDocument()
    expect(screen.getByText("Connector")).toBeInTheDocument()
  })

  it("selects a preset and fills the input", () => {
    render(<ChatSidebar />)
    fireEvent.click(screen.getByRole("button", { name: "Toggle prompt presets" }))
    fireEvent.click(screen.getByText("Enclosure"))
    expect(screen.getByDisplayValue(/Create a rectangular enclosure/)).toBeInTheDocument()
  })

  it("sends a prompt when send button is clicked", () => {
    const onSendPrompt = jest.fn()
    render(<ChatSidebar onSendPrompt={onSendPrompt} />)

    const textarea = screen.getByPlaceholderText("Describe the 3D model you want to generate...")
    fireEvent.change(textarea, { target: { value: "Create a bracket" } })
    fireEvent.click(screen.getByRole("button", { name: "Send message" }))

    expect(onSendPrompt).toHaveBeenCalledWith("Create a bracket")
  })

  it("sends a prompt on Enter key", () => {
    const onSendPrompt = jest.fn()
    render(<ChatSidebar onSendPrompt={onSendPrompt} />)

    const textarea = screen.getByPlaceholderText("Describe the 3D model you want to generate...")
    fireEvent.change(textarea, { target: { value: "Create a bracket" } })
    fireEvent.keyDown(textarea, { key: "Enter", code: "Enter" })

    expect(onSendPrompt).toHaveBeenCalledWith("Create a bracket")
  })

  it("switches to revisions tab", () => {
    render(<ChatSidebar />)

    fireEvent.click(screen.getByRole("button", { name: "Revisions" }))
    expect(screen.getByText("No revision history yet")).toBeInTheDocument()
  })

  it("switches to auto-fix tab", () => {
    render(<ChatSidebar />)

    fireEvent.click(screen.getByRole("button", { name: "Auto-Fix" }))
    expect(screen.getByText("Idle")).toBeInTheDocument()
  })

  it("renders initial messages", () => {
    const initialMessages = [
      {
        id: "msg-1",
        role: "user" as const,
        content: "Hello",
        timestamp: new Date(),
      },
      {
        id: "msg-2",
        role: "assistant" as const,
        content: "Hi there!",
        timestamp: new Date(),
      },
    ]
    render(<ChatSidebar initialMessages={initialMessages} />)

    expect(screen.getByText("Hello")).toBeInTheDocument()
    expect(screen.getByText("Hi there!")).toBeInTheDocument()
  })

  it("calls onSelectRevision when a revision is selected", () => {
    const onSelectRevision = jest.fn()
    const revisions = [
      {
        id: "rev-1",
        prompt: "Create a gear",
        modelName: "gear.step",
        timestamp: new Date(),
        parameters: {},
      },
    ]

    render(
      <ChatSidebar
        revisions={revisions}
        onSelectRevision={onSelectRevision}
      />
    )

    fireEvent.click(screen.getByRole("button", { name: "Revisions" }))
    fireEvent.click(screen.getByText("Create a gear"))

    expect(onSelectRevision).toHaveBeenCalledWith(revisions[0])
  })

  it("calls onClearRevisions when clear is clicked", () => {
    const onClearRevisions = jest.fn()
    const revisions = [
      {
        id: "rev-1",
        prompt: "Create a gear",
        modelName: "gear.step",
        timestamp: new Date(),
        parameters: {},
      },
    ]

    render(
      <ChatSidebar
        revisions={revisions}
        onClearRevisions={onClearRevisions}
      />
    )

    fireEvent.click(screen.getByRole("button", { name: "Revisions" }))
    fireEvent.click(screen.getByRole("button", { name: "Clear revision history" }))

    expect(onClearRevisions).toHaveBeenCalled()
  })
})
