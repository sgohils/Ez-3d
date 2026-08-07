import { appApi } from "../api"

describe("AppApiService.exportModel", () => {
  const originalBaseUrl = (appApi as any).baseUrl

  beforeEach(() => {
    ;(appApi as any).baseUrl = "http://localhost:8000"
    global.fetch = jest.fn()
  })

  afterEach(() => {
    ;(appApi as any).baseUrl = originalBaseUrl
    jest.resetAllMocks()
  })

  it("constructs URL with format query param using template literal", async () => {
    const mockResponse = {
      ok: true,
      blob: () => Promise.resolve(new Blob()),
    }
    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    await appApi.exportModel("step")

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/export?format=step",
    )
  })

  it("appends tolerance when provided", async () => {
    const mockResponse = {
      ok: true,
      blob: () => Promise.resolve(new Blob()),
    }
    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    await appApi.exportModel("stl", 0.01)

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/export?format=stl&tolerance=0.01",
    )
  })

  it("throws APIError when response is not ok", async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      text: () => Promise.resolve("Export failed"),
    }
    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    await expect(appApi.exportModel("gltf")).rejects.toThrow("Export failed")
  })
})
