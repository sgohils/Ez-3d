"use client"

import { useState } from "react"
import { AppProvider, useApp } from "@/contexts/AppContext"
import { GlobalErrorBoundary } from "@/components/GlobalErrorBoundary"
import { ChatSidebar } from "@/components/chat/ChatSidebar"
import { ParametricPanel } from "@/components/controls/ParametricPanel"
import { CodeDrawer } from "@/components/editor/CodeDrawer"
import { CADViewport } from "@/components/viewport/Scene"
import { LoadingSpinner } from "@/components/ui/LoadingSpinner"
import { ToastContainer, type Toast } from "@/components/ui/Toast"
import { appApi } from "@/lib/api"
import { MessageSquare, Code2, Download, PanelRightClose, PanelRightOpen } from "lucide-react"
import type { Message, Revision, AutoFixState } from "@/components/chat/types"
import type { CodeVariable } from "@/components/editor/LiveSync"

function AppLayout() {
  const {
    modelUrl,
    code,
    parameters,
    variables,
    loading,
    isGenerating,
    isRecompiling,
    chatHistory,
    revisions,
    autoFixState,
    errors,
    sendPrompt,
    updateCode,
    removeError,
    clearErrors,
    selectRevision,
    clearRevisions,
  } = useApp()

  const [codeDrawerOpen, setCodeDrawerOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [showRightPanel, setShowRightPanel] = useState(true)

  const handleExport = async (format: "step" | "stl" | "gltf") => {
    if (!modelUrl) return
    setExporting(true)
    try {
      const blob = await appApi.exportModel(format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `model.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `Failed to export ${format.toUpperCase()}`
      removeError(errors.findIndex((e) => e.includes(errorMessage.slice(0, 20))))
    } finally {
      setExporting(false)
    }
  }

  const handleSelectRevision = (revision: Revision) => {
    selectRevision(revision)
  }

  const handleClearRevisions = () => {
    clearRevisions()
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-950">
      {/* Left Sidebar - Chat */}
      <div className="w-[320px] flex-shrink-0 border-r border-gray-800 bg-gray-900 flex flex-col">
        <ChatSidebar
          initialMessages={chatHistory}
          revisions={revisions}
          autoFixState={autoFixState}
          onSendPrompt={sendPrompt}
          onSelectRevision={handleSelectRevision}
          onClearRevisions={handleClearRevisions}
        />
      </div>

      {/* Center - Viewport */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Toolbar */}
        <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between pointer-events-none">
          <div className="pointer-events-auto flex items-center gap-2">
            <div className="bg-gray-900/90 backdrop-blur-sm border border-gray-700 rounded-lg px-3 py-1.5">
              <h1 className="text-sm font-semibold text-gray-100">CADGen AI</h1>
            </div>
          </div>
          <div className="pointer-events-auto flex items-center gap-2">
            {modelUrl && (
              <>
                <button
                  onClick={() => handleExport("gltf")}
                  disabled={exporting}
                  className="flex items-center gap-1.5 bg-gray-900/90 backdrop-blur-sm border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  GLTF
                </button>
                <button
                  onClick={() => handleExport("stl")}
                  disabled={exporting}
                  className="flex items-center gap-1.5 bg-gray-900/90 backdrop-blur-sm border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  STL
                </button>
                <button
                  onClick={() => handleExport("step")}
                  disabled={exporting}
                  className="flex items-center gap-1.5 bg-gray-900/90 backdrop-blur-sm border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  STEP
                </button>
              </>
            )}
            <button
              onClick={() => setShowRightPanel(!showRightPanel)}
              className="bg-gray-900/90 backdrop-blur-sm border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white p-1.5 rounded-lg transition-colors"
              title={showRightPanel ? "Hide panel" : "Show panel"}
            >
              {showRightPanel ? (
                <PanelRightClose className="w-4 h-4" />
              ) : (
                <PanelRightOpen className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Viewport */}
        <div className="flex-1 relative">
          {isGenerating && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-gray-950/50 backdrop-blur-sm">
              <div className="flex flex-col items-center gap-3">
                <LoadingSpinner size={40} />
                <p className="text-sm text-gray-300">Generating model...</p>
              </div>
            </div>
          )}
          <CADViewport
            modelUrl={modelUrl ?? undefined}
            displayMode="shaded"
            lighting="warehouse"
            showGrid={true}
            showAxes={true}
            showStats={false}
            showEnvironment={true}
            enableClipping={false}
            autoRotate={false}
            enableDamping={true}
          />
        </div>
      </div>

      {/* Right Panel - Controls */}
      {showRightPanel && (
        <div className="w-[320px] flex-shrink-0 border-l border-gray-800 bg-gray-900 flex flex-col overflow-hidden">
          {/* Parametric Panel */}
          <div className="flex-1 overflow-y-auto">
            <ParametricPanel />
          </div>

          {/* Code Drawer Toggle */}
          <div className="border-t border-gray-800 p-3">
            <button
              onClick={() => setCodeDrawerOpen(true)}
              disabled={!code}
              className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-800 disabled:opacity-40 text-gray-300 hover:text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Code2 className="w-4 h-4" />
              View Code
            </button>
          </div>
        </div>
      )}

      {/* Code Drawer Overlay */}
      <CodeDrawer
        isOpen={codeDrawerOpen}
        onClose={() => setCodeDrawerOpen(false)}
        code={code}
        onCodeChange={updateCode}
        readOnly={true}
      />

      {/* Loading overlay for recompile */}
      {isRecompiling && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-2 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 shadow-lg">
            <LoadingSpinner size={16} />
            <span className="text-sm text-gray-300">Recompiling...</span>
          </div>
        </div>
      )}

      {/* Export progress overlay */}
      {exporting && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50">
          <div className="flex items-center gap-2 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 shadow-lg">
            <LoadingSpinner size={16} />
            <span className="text-sm text-gray-300">Exporting...</span>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <ToastContainer
        toasts={errors.map((message, index) => ({
          id: `error-${index}`,
          message,
          type: "error" as const,
        }))}
        onDismiss={(id) => {
          const index = parseInt(id.replace("error-", ""), 10)
          removeError(index)
        }}
      />
    </div>
  )
}

export default function Page() {
  return (
    <GlobalErrorBoundary>
      <AppProvider>
        <AppLayout />
      </AppProvider>
    </GlobalErrorBoundary>
  )
}
