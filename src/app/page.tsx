"use client"

import { useState, useCallback } from "react"
import { CodeDrawer } from "@/components/editor"
import { ChatSidebar } from "@/components/chat"
import { type CodeVariable } from "@/components/editor/LiveSync"

const DEFAULT_CODE = `import cadquery as cq
from cadquery import Workplane

width: float = 50
height: float = 50
thickness: float = 10
hole_diameter: float = 10

result = (
    cq.Workplane("XY")
    .box(width, height, thickness)
    .faces(">Z")
    .workplane()
    .hole(hole_diameter)
)

show_object(result)
`

export default function Page() {
  const [code, setCode] = useState(DEFAULT_CODE)
  const [modelUrl, setModelUrl] = useState("")
  const [parameters, setParameters] = useState<Record<string, number>>({})
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const handleCodeChange = useCallback((newCode: string) => {
    setCode(newCode)
  }, [])

  const handleVariablesExtracted = useCallback((variables: CodeVariable[]) => {
    const newParams: Record<string, number> = {}
    for (const v of variables) {
      newParams[v.name] = v.value
    }
    setParameters(newParams)
  }, [])

  const handleVariableUpdate = useCallback((name: string, value: number) => {
    setParameters((prev) => ({ ...prev, [name]: value }))
  }, [])

  const handleRecompileSuccess = useCallback(
    (result: {
      code: string
      gltfUrl: string
      stlUrl: string
      stepUrl: string
      logs: string
    }) => {
      if (result.gltfUrl) {
        setModelUrl(result.gltfUrl)
      } else if (result.stlUrl) {
        setModelUrl(result.stlUrl)
      } else if (result.stepUrl) {
        setModelUrl(result.stepUrl)
      }
    },
    [],
  )

  const handleSendPrompt = useCallback((prompt: string) => {
    console.log("Send prompt:", prompt)
  }, [])

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <div className="w-[300px] flex-shrink-0 border-r border-gray-700">
        <ChatSidebar onSendPrompt={handleSendPrompt} />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <h1 className="text-sm font-semibold text-gray-100">CADGen AI</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsDrawerOpen(true)}
              className="px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
            >
              Open Code Editor
            </button>
          </div>
        </div>

        <div className="flex-1 flex items-center justify-center">
          {modelUrl ? (
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-2">Model loaded:</p>
              <p className="text-xs text-blue-400 font-mono break-all max-w-md">
                {modelUrl}
              </p>
              <p className="text-xs text-gray-500 mt-4">
                (CADViewport placeholder — model URL ready for 3D rendering)
              </p>
            </div>
          ) : (
            <div className="text-center text-gray-500">
              <p className="text-sm">No model loaded</p>
              <p className="text-xs mt-1">Send a prompt to generate a model</p>
            </div>
          )}
        </div>
      </div>

      <div className="w-[320px] flex-shrink-0 border-l border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Parameters
          </h2>
        </div>
        <div className="p-4">
          {Object.keys(parameters).length === 0 ? (
            <p className="text-xs text-gray-500">No parameters detected</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(parameters).map(([name, value]) => (
                <div key={name} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-gray-300 font-mono">{name}</label>
                    <span className="text-xs text-gray-400 font-mono w-16 text-right">
                      {value.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-700 rounded-lg" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <CodeDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        code={code}
        onCodeChange={handleCodeChange}
        onVariablesExtracted={handleVariablesExtracted}
        onVariableUpdate={handleVariableUpdate}
        onRecompileSuccess={handleRecompileSuccess}
        readOnly={false}
      />
    </div>
  )
}
