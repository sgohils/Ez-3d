import httpx
from pydantic import BaseModel, Field


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4096

CADQUERY_PROMPT_TEMPLATE = """You are a CadQuery Python code generator. Generate clean, executable CadQuery Python code that produces a 3D CAD model.

Follow this exact structure:

1. Dynamic Parameters Section (at the top of the file):
   Define all parametric variables with [slider: min-max, step: X] annotations on the line above each variable.
   Example:
   # [slider: 10-100, step: 5]
   width = 50

2. Geometry Construction Section:
   Use CadQuery (cq) to build the 3D geometry. Import cadquery as cq.
   Use the parameters defined above to drive the geometry.

3. Export Statements (at the end of the file):
   Export the model in STEP and STL format.
   Example:
   cq.exporters.export(result, "model.step")
   cq.exporters.export(result, "model.stl")

Rules:
- The code must be valid Python 3.11+ and use only the cadquery library.
- All parameters must be defined at the top with [slider: min-max, step: X] annotations.
- The final exported object must be named `result`.
- Do not include any print statements or debug code.
- Do not include any comments except for the slider annotations.
- The code must be executable as-is by CadQuery.

User prompt: {prompt}

Generate the CadQuery Python code now:"""


class LLMConfig(BaseModel):
    base_url: str = Field(default=DEFAULT_BASE_URL, description="OpenAI-compatible API base URL")
    model: str = Field(default=DEFAULT_MODEL, description="Model to use for code generation")
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS, ge=1, le=16384)
    api_key: str | None = Field(default=None, description="API key for authentication")


class LLMResponse(BaseModel):
    code: str
    usage: dict[str, int] | None = None


class LLMClient:
    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=httpx.Timeout(120.0),
            )
        return self._client

    def _build_messages(self, prompt: str) -> list[dict[str, str]]:
        system_message = (
            "You are a CadQuery Python code generator. "
            "Generate clean, executable CadQuery Python code following the standard template: "
            "dynamic parameters section with [slider: min-max, step: X] annotations, "
            "geometry construction using cadquery, and export statements."
        )
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": CADQUERY_PROMPT_TEMPLATE.format(prompt=prompt)},
        ]

    async def generate_code(self, prompt: str) -> LLMResponse:
        client = self._get_client()
        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": self._build_messages(prompt),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]
        code = choice["message"]["content"]
        usage = data.get("usage")
        return LLMResponse(code=code, usage=usage if usage else None)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "LLMClient":
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        await self.close()