"use client"

import { useState, useRef, useCallback } from "react"
import { Send, ChevronDown, ChevronUp, Hash, X } from "lucide-react"
import { type PromptPreset } from "./types"

interface PromptInputProps {
  onSend: (prompt: string) => void
  presets: PromptPreset[]
  isLoading?: boolean
  maxChars?: number
}

export function PromptInput({
  onSend,
  presets,
  isLoading = false,
  maxChars = 500,
}: PromptInputProps) {
  const [input, setInput] = useState("")
  const [showPresets, setShowPresets] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const presetRef = useRef<HTMLDivElement>(null)

  const charCount = input.length
  const isOverLimit = charCount > maxChars
  const canSend = input.trim().length > 0 && !isOverLimit && !isLoading

  const handleSend = useCallback(() => {
    if (!canSend) return
    onSend(input.trim())
    setInput("")
    textareaRef.current?.focus()
  }, [input, canSend, onSend])

  const handlePresetSelect = useCallback(
    (prompt: string) => {
      setInput(prompt)
      setShowPresets(false)
      textareaRef.current?.focus()
    },
    [],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  return (
    <div className="border-t border-gray-800 bg-gray-900 p-3">
      {showPresets && presets.length > 0 && (
        <div
          ref={presetRef}
          className="mb-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg overflow-hidden"
        >
          <div className="px-3 py-2 border-b border-gray-700 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              Prompt Presets
            </span>
            <button
              onClick={() => setShowPresets(false)}
              className="p-0.5 hover:bg-gray-700 rounded"
              aria-label="Close presets"
            >
              <X className="w-3 h-3 text-gray-400" />
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto">
            {presets.map((preset) => (
              <button
                key={preset.name}
                onClick={() => handlePresetSelect(preset.prompt)}
                className="w-full text-left px-3 py-2 hover:bg-gray-700 transition-colors border-b border-gray-700 last:border-b-0"
              >
                <div className="text-sm font-medium text-gray-100">{preset.label}</div>
                <div className="text-xs text-gray-400 mt-0.5">{preset.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the 3D model you want to generate..."
            maxLength={maxChars}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500 transition-shadow"
          />
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            <button
              onClick={() => setShowPresets(!showPresets)}
              className={`p-1 rounded transition-colors ${
                showPresets ? "bg-blue-900/50 text-blue-400" : "text-gray-400 hover:text-gray-200"
              }`}
              aria-label="Toggle prompt presets"
            >
              {showPresets ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        <button
          onClick={handleSend}
          disabled={!canSend}
          className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-800 disabled:text-blue-300 disabled:cursor-not-allowed transition-colors"
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-3">
          {presets.length > 0 && (
            <button
              onClick={() => setShowPresets(!showPresets)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
            >
              <Hash className="w-3 h-3" />
              Presets
            </button>
          )}
        </div>
        <span
          className={`text-xs font-mono ${
            isOverLimit ? "text-red-400" : charCount > maxChars * 0.8 ? "text-yellow-400" : "text-gray-500"
          }`}
        >
          {charCount}/{maxChars}
        </span>
      </div>
    </div>
  )
}
