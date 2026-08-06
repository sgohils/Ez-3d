"use client"

import { useState, useCallback } from "react"
import { apiService } from "@/lib/api/client"
import { type GenerateResult } from "@/hooks/useApi"
import { MessageList } from "./MessageList"
import { PromptInput } from "./PromptInput"
import { RevisionHistory } from "./RevisionHistory"
import { AutoFixIndicator } from "./AutoFixIndicator"
import { type Message, type PromptPreset, type Revision, type AutoFixState } from "./types"

const DEFAULT_PRESETS: PromptPreset[] = [
  {
    name: "enclosure",
    label: "Enclosure",
    description: "Generate a parametric enclosure with removable lid",
    prompt: "Create a rectangular enclosure with a removable lid, 80mm x 60mm x 40mm, with mounting holes on the base and snap-fit features on the lid",
  },
  {
    name: "mounting_bracket",
    label: "Mounting Bracket",
    description: "Generate a wall-mount bracket with adjustable angles",
    prompt: "Create a wall-mounting bracket with adjustable angle, 120mm x 80mm x 30mm, with two mounting holes and a slotted adjustment slot",
  },
  {
    name: "spur_gear",
    label: "Spur Gear",
    description: "Generate a spur gear with configurable teeth and module",
    prompt: "Create a spur gear with 20 teeth, module 2mm, 10mm thickness, with a central bore hole of 5mm",
  },
  {
    name: "bearing_housing",
    label: "Bearing Housing",
    description: "Generate a housing for a standard bearing",
    prompt: "Create a bearing housing for a 6205 deep groove ball bearing, with mounting flanges and a shaft hole of 25mm",
  },
  {
    name: "connector",
    label: "Connector",
    description: "Generate a simple connector block",
    prompt: "Create a connector block with two aligned bores of 8mm and four mounting holes, 40mm x 30mm x 20mm",
  },
]

const DEFAULT_PRESETS_SPARE: PromptPreset[] = [
  {
    name: "flywheel",
    label: "Flywheel",
    description: "Generate a heavy flywheel with rim and hub",
    prompt: "Create a flywheel with a 60mm outer radius, 20mm inner bore, 15mm thickness, with 4 mounting holes on a 50mm bolt circle",
  },
  {
    name: "coupling",
    label: "Coupling",
    description: "Generate a shaft coupling with set screws",
    prompt: "Create a shaft coupling for 10mm shafts, 40mm length, with 2 set screws and a keyway",
  },
  {
    name: "bracket",
    label: "L-Bracket",
    description: "Generate an L-shaped mounting bracket",
    prompt: "Create an L-shaped bracket, 100mm x 100mm x 50mm, with 4 mounting holes and a 12mm clearance hole",
  },
]

interface ChatSidebarProps {
  initialMessages?: Message[]
  presets?: PromptPreset[]
  autoFixState?: AutoFixState
  revisions?: Revision[]
  onSendPrompt?: (prompt: string) => void
  onSelectRevision?: (revision: Revision) => void
  onClearRevisions?: () => void
}

export function ChatSidebar({
  initialMessages = [],
  presets = DEFAULT_PRESETS,
  autoFixState = { status: "idle", logs: [], currentIteration: 0, totalIterations: 0 },
  revisions = [],
  onSendPrompt,
  onSelectRevision,
  onClearRevisions,
}: ChatSidebarProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<"chat" | "revisions" | "autofix">("chat")

  const handleSend = useCallback(
    async (prompt: string) => {
      const userMessage: Message = {
        id: `msg-${Date.now()}-user`,
        role: "user",
        content: prompt,
        timestamp: new Date(),
      }

      const loadingMessage: Message = {
        id: `msg-${Date.now()}-loading`,
        role: "system",
        content: "Generating model...",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage, loadingMessage])
      setIsLoading(true)

      try {
        const result: GenerateResult = await apiService.generate(prompt)
        setMessages((prev) => {
          const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id)
          const assistantMessage: Message = {
            id: `msg-${Date.now()}-assistant`,
            role: "assistant",
            content: `Generated model based on: "${prompt}"`,
            timestamp: new Date(),
            codePreview: result.code,
            modelInfo: {
              step_url: result.step_url,
              stl_url: result.stl_url,
              gltf_url: result.gltf_url,
              parameters: result.parameters,
              code: result.code,
              logs: result.logs,
            },
          }
          return [...withoutLoading, assistantMessage]
        })
        onSendPrompt?.(prompt)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error"
        const detail = err && typeof err === "object" && "detail" in err ? String(err.detail) : ""
        setMessages((prev) => {
          const withoutLoading = prev.filter((m) => m.id !== loadingMessage.id)
          const systemMessage: Message = {
            id: `msg-${Date.now()}-error`,
            role: "system",
            content: `Generation failed: ${errorMessage}${detail ? `\n${detail}` : ""}`,
            timestamp: new Date(),
          }
          return [...withoutLoading, systemMessage]
        })
      } finally {
        setIsLoading(false)
      }
    },
    [onSendPrompt],
  )

  const handleSelectRevision = useCallback(
    (revision: Revision) => {
      onSelectRevision?.(revision)
    },
    [onSelectRevision],
  )

  const handleClearRevisions = useCallback(() => {
    onClearRevisions?.()
  }, [onClearRevisions])

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-900">Chat</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab("chat")}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              activeTab === "chat"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => setActiveTab("revisions")}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              activeTab === "revisions"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            Revisions
          </button>
          <button
            onClick={() => setActiveTab("autofix")}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              activeTab === "autofix"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            Auto-Fix
          </button>
        </div>
      </div>

      {activeTab === "chat" && (
        <>
          <MessageList messages={messages} isLoading={isLoading} />
          <PromptInput
            onSend={handleSend}
            presets={presets}
            isLoading={isLoading || autoFixState.status === "running"}
          />
        </>
      )}

      {activeTab === "revisions" && (
        <RevisionHistory
          revisions={revisions}
          onSelectRevision={handleSelectRevision}
          onClear={handleClearRevisions}
        />
      )}

      {activeTab === "autofix" && <AutoFixIndicator state={autoFixState} />}
    </div>
  )
}
