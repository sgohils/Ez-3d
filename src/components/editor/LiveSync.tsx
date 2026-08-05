export interface CodeVariable {
  name: string
  value: number
  min: number
  max: number
  step: number
  line: number
}

export interface LiveSyncProps {
  code: string
  onCodeChange: (code: string) => void
  onVariablesExtracted: (variables: CodeVariable[]) => void
  onVariableUpdate: (name: string, value: number) => void
  readOnly?: boolean
}

const VARIABLE_PATTERN =
  /^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(?:#.*)?$/gm

const TYPE_ANNOTATION_PATTERN =
  /^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(float|int|Decimal)\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\s*(?:#.*)?$/gm

export function extractVariables(code: string): CodeVariable[] {
  const variables: CodeVariable[] = []
  const seen = new Set<string>()

  let match: RegExpExecArray | null

  while ((match = TYPE_ANNOTATION_PATTERN.exec(code)) !== null) {
    const name = match[1]
    const value = parseFloat(match[3])
    if (!seen.has(name) && Number.isFinite(value)) {
      seen.add(name)
      const { min, max, step } = inferRange(name, value)
      variables.push({
        name,
        value,
        min,
        max,
        step,
        line: code.slice(0, match.index).split("\n").length,
      })
    }
  }

  VARIABLE_PATTERN.lastIndex = 0
  while ((match = VARIABLE_PATTERN.exec(code)) !== null) {
    const name = match[1]
    const value = parseFloat(match[2])
    if (!seen.has(name) && Number.isFinite(value)) {
      seen.add(name)
      const { min, max, step } = inferRange(name, value)
      variables.push({
        name,
        value,
        min,
        max,
        step,
        line: code.slice(0, match.index).split("\n").length,
      })
    }
  }

  return variables.sort((a, b) => a.line - b.line)
}

function inferRange(name: string, value: number): { min: number; max: number; step: number } {
  const absValue = Math.abs(value)

  if (absValue === 0) {
    return { min: 0, max: 100, step: 1 }
  }

  let min: number
  let max: number
  let step: number

  if (absValue >= 1000) {
    min = 0
    max = Math.ceil(absValue * 2 / 1000) * 1000
    step = Math.max(1, Math.floor(max / 100))
  } else if (absValue >= 100) {
    min = 0
    max = Math.ceil(absValue * 2 / 100) * 100
    step = Math.max(1, Math.floor(max / 100))
  } else if (absValue >= 10) {
    min = 0
    max = Math.ceil(absValue * 2 / 10) * 10
    step = Math.max(0.1, Math.floor(max / 100) / 10)
  } else if (absValue >= 1) {
    min = 0
    max = Math.ceil(absValue * 2)
    step = 0.1
  } else {
    min = 0
    max = Math.ceil(absValue * 2 * 10) / 10
    step = 0.01
  }

  if (name.toLowerCase().includes("angle") || name.toLowerCase().includes("deg")) {
    min = 0
    max = 360
    step = 1
  } else if (name.toLowerCase().includes("radius") || name.toLowerCase().includes("diameter")) {
    min = 0
    max = Math.ceil(absValue * 3)
    step = 0.1
  } else if (name.toLowerCase().includes("height") || name.toLowerCase().includes("length")) {
    min = 0
    max = Math.ceil(absValue * 3)
    step = 0.1
  } else if (name.toLowerCase().includes("thick") || name.toLowerCase().includes("width")) {
    min = 0
    max = Math.ceil(absValue * 3)
    step = 0.1
  } else if (name.toLowerCase().includes("hole") || name.toLowerCase().includes("count")) {
    min = 1
    max = Math.max(100, Math.ceil(absValue * 3))
    step = 1
  }

  if (value < 0) {
    const tmp = min
    min = -max
    max = -tmp
  }

  step = Number(step.toFixed(10))

  return { min, max, step }
}

export function updateVariableInCode(code: string, name: string, newValue: number): string {
  const lines = code.split("\n")
  const updatedLines = lines.map((line) => {
    const assignmentMatch = line.match(
      new RegExp(`^\\s*(${escapeRegex(name)})\\s*[:=]\\s*([+-]?\\d*\\.?\\d+(?:[eE][+-]?\\d+)?)`),
    )
    if (assignmentMatch) {
      const indent = line.match(/^\s*/)?.[0] || ""
      const rest = line.slice(assignmentMatch[0].length).trim()
      return `${indent}${name} = ${formatNumber(newValue)}${rest ? "  # " + rest : ""}`
    }
    return line
  })
  return updatedLines.join("\n")
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

function formatNumber(num: number): string {
  if (Number.isInteger(num)) {
    return num.toString()
  }
  const formatted = num.toFixed(6)
  return formatted.replace(/0+$/, "").replace(/\.$/, "")
}
