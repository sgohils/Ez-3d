import traceback
from dataclasses import dataclass, field

from .llm_client import LLMClient, LLMConfig, LLMResponse

MAX_RETRIES = 3

SYSTEM_PROMPT_REPAIR = """The previously generated CadQuery code failed to execute with the following error:

{error_trace}

Original code:
{original_code}

Fix the code and return only the corrected CadQuery Python code. Do not include any explanation or extra text. Ensure all [slider: min-max, step: X] annotations are preserved and the code follows the standard template: dynamic parameters section, geometry construction, export statements."""


@dataclass
class CorrectionAttempt:
    attempt: int
    code: str
    error: str | None = None
    success: bool = False
    response: LLMResponse | None = None


@dataclass
class CorrectionResult:
    code: str
    attempts: list[CorrectionAttempt] = field(default_factory=list)
    success: bool = False
    final_error: str | None = None


class SelfCorrectionLoop:
    def __init__(self, client: LLMClient, max_retries: int = MAX_RETRIES) -> None:
        self.client = client
        self.max_retries = max_retries

    async def execute_with_correction(self, prompt: str, executor: callable) -> CorrectionResult:
        result = CorrectionResult()
        current_prompt = prompt

        for attempt_num in range(1, self.max_retries + 1):
            attempt = CorrectionAttempt(attempt=attempt_num, code=current_prompt)
            result.attempts.append(attempt)

            try:
                llm_response = await self.client.generate_code(current_prompt)
                attempt.response = llm_response
                attempt.code = llm_response.code

                exec_result = await executor(llm_response.code)
                attempt.success = True
                result.code = llm_response.code
                result.success = True
                return result

            except Exception as exc:
                error_trace = traceback.format_exc()
                attempt.error = error_trace

                if attempt_num >= self.max_retries:
                    result.final_error = error_trace
                    break

                current_prompt = SYSTEM_PROMPT_REPAIR.format(
                    error_trace=error_trace,
                    original_code=llm_response.code if attempt.response else current_prompt,
                )

        result.code = current_prompt
        return result