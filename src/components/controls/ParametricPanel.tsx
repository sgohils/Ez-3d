"use client"

interface Parameter {
  name: string
  value: number
  min: number
  max: number
  step: number
}

interface ParametricPanelProps {
  parameters: Parameter[]
  onChange: (params: Array<{ name: string; value: number }>) => void
}

export const ParametricPanel = ({ parameters, onChange }: ParametricPanelProps) => {
  const handleChange = (name: string, value: number) => {
    onChange(parameters.map((p) => (p.name === name ? { name: p.name, value } : p)))
  }

  return (
    <div className="bg-gray-900 text-gray-100 rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        Parameters
      </h2>
      {parameters.length === 0 ? (
        <p className="text-gray-500 text-sm">No parameters</p>
      ) : (
        <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto pr-1">
          {parameters.map((param) => (
            <div key={param.name} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-gray-300">{param.name}</span>
                <span className="font-mono text-xs text-blue-400 text-right w-16">
                  {param.value.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={param.min}
                max={param.max}
                step={param.step}
                value={param.value}
                onChange={(e) => handleChange(param.name, parseFloat(e.target.value))}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
