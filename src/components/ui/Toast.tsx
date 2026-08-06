"use client"

import { X, AlertCircle, CheckCircle, Info } from "lucide-react"

export type ToastType = "error" | "success" | "info"

export interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastItemProps {
  toast: Toast
  onDismiss: (id: string) => void
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const iconMap = {
    error: <AlertCircle className="w-4 h-4 flex-shrink-0" />,
    success: <CheckCircle className="w-4 h-4 flex-shrink-0" />,
    info: <Info className="w-4 h-4 flex-shrink-0" />,
  }

  const colorMap = {
    error: "bg-red-50 border-red-200 text-red-800",
    success: "bg-green-50 border-green-200 text-green-800",
    info: "bg-blue-50 border-blue-200 text-blue-800",
  }

  const iconColorMap = {
    error: "text-red-500",
    success: "text-green-500",
    info: "text-blue-500",
  }

  return (
    <div
      className={`flex items-start gap-2 px-4 py-3 rounded-lg border shadow-sm animate-in slide-in-from-right-2 fade-in ${colorMap[toast.type]}`}
      role="alert"
    >
      <span className={iconColorMap[toast.type]}>{iconMap[toast.type]}</span>
      <p className="text-sm flex-1">{toast.message}</p>
      <button
        onClick={() => onDismiss(toast.id)}
        className="flex-shrink-0 p-0.5 rounded hover:bg-black/5 transition-colors"
        aria-label="Dismiss"
      >
        <X className="w-3.5 h-3.5 opacity-60 hover:opacity-100" />
      </button>
    </div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onDismiss: (id: string) => void
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
