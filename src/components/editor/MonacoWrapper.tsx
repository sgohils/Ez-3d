import Editor from "@monaco-editor/react"

interface MonacoWrapperProps {
  value: string
  onChange?: (value: string | undefined) => void
  language?: string
  readOnly?: boolean
  height?: string | number
  options?: Record<string, unknown>
}

export function MonacoWrapper({
  value,
  onChange,
  language = "python",
  readOnly = true,
  height = "100%",
  options = {},
}: MonacoWrapperProps) {
  return (
    <Editor
      height={height}
      language={language}
      theme="vs-dark"
      value={value}
      onChange={onChange}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 13,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        wordWrap: "on",
        padding: { top: 12 },
        ...options,
      }}
    />
  )
}
