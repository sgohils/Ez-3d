"use client"

import { Component, ReactNode } from "react"

interface GlobalErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface GlobalErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class GlobalErrorBoundary extends Component<
  GlobalErrorBoundaryProps,
  GlobalErrorBoundaryState
> {
  state: GlobalErrorBoundaryState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): GlobalErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error("Global error boundary caught:", error, errorInfo)
  }

  reset = () => this.setState({ hasError: false, error: null })

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return (
        <div className="flex h-screen w-screen items-center justify-center bg-gray-950">
          <div className="max-w-md rounded-lg border border-red-500/50 bg-gray-900 p-6 shadow-lg">
            <h2 className="mb-2 text-lg font-semibold text-red-400">
              Something went wrong
            </h2>
            <p className="mb-4 text-sm text-gray-400">
              The application encountered an unexpected error. You can try
              reloading the page.
            </p>
            <pre className="mb-4 overflow-auto rounded bg-gray-800 p-3 text-xs text-red-300">
              {this.state.error?.message || "Unknown error"}
            </pre>
            <button
              onClick={this.reset}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
