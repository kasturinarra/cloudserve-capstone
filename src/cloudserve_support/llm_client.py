import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(".env")


class LLMProviderError(RuntimeError):
    """Raised when the model provider cannot complete a request."""


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = os.environ["MODEL_NAME"]

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise LLMProviderError(
                f"LLM provider request failed: {type(exc).__name__}: {exc}"
            ) from exc

        content = response.choices[0].message.content

        if not content:
            raise LLMProviderError(
                "LLM provider returned an empty response."
            )

        return content
