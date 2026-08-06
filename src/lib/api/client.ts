import { APIError } from "@/lib/types"

export class ApiService {
  protected baseUrl: string

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") {
    this.baseUrl = baseUrl
  }

  async generate(prompt: string, parameters?: Record<string, unknown>): Promise<any> {
    return this.request("/api/v1/generate", "POST", { prompt, parameters })
  }

  async recompile(parameters: Record<string, unknown>): Promise<any> {
    return this.request("/api/v1/recompile", "POST", { parameters })
  }

  async exportModel(format: "step" | "stl" | "gltf"): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/v1/export?format=${format}`)
    if (!response.ok) {
      throw new APIError("Export failed", response.status)
    }
    return response.blob()
  }

  protected async request(path: string, method: string, body?: any): Promise<any> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      throw new APIError("Request failed", response.status, await response.text())
    }

    return response.json()
  }
}

export const apiService = new ApiService()
