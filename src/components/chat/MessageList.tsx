"use client"

import Image from "next/image"
import { type Message } from "./types"
import { BotMessageSquare, Code2, ImageIcon } from "lucide-react"

interface MessageListProps {
  messages: Message[]
}

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
        <div className="text-center">
          <BotMessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No messages yet</p>
          <p className="text-xs mt-1">Start a conversation to generate 3D models</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${
              message.role === "user"
                ? "bg-blue-600 text-white"
                : message.role === "system"
                  ? "bg-gray-800 text-gray-300"
                  : "bg-gray-800 text-gray-100"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              {message.role === "user" && (
                <span className="font-medium text-xs uppercase tracking-wider opacity-75">
                  You
                </span>
              )}
              {message.role === "assistant" && (
                <span className="font-medium text-xs uppercase tracking-wider opacity-75">
                  Assistant
                </span>
              )}
              {message.role === "system" && (
                <span className="font-medium text-xs uppercase tracking-wider opacity-75">
                  System
                </span>
              )}
              <span className="text-[10px] opacity-50">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </div>
            <p className="whitespace-pre-wrap">{message.content}</p>
            {message.imageUrl && (
              <div className="mt-2 rounded overflow-hidden border border-gray-700 relative">
                <Image
                  src={message.imageUrl}
                  alt="Generated model preview"
                  className="w-full h-auto max-h-48 object-contain"
                  width={400}
                  height={300}
                />
              </div>
            )}
            {message.codePreview && (
              <div className="mt-2 rounded bg-gray-950 border border-gray-700 overflow-hidden">
                <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-gray-700">
                  <Code2 className="w-3 h-3 text-gray-400" />
                  <span className="text-[10px] text-gray-400 font-medium uppercase">
                    Generated Code
                  </span>
                </div>
                <pre className="p-3 text-xs font-mono text-gray-300 overflow-x-auto max-h-32">
                  <code>{message.codePreview}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
