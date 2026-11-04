"""Provider-agnostic OpenAI-compatible AI client with retry handling."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class AIError(Exception):
    """Raised when the upstream AI service fails."""


class AIService:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 60.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def complete(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        endpoint = f"{self.base_url}/chat/completions"

        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(3):
                try:
                    resp = await client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                except (httpx.RequestError, httpx.HTTPStatusError, KeyError, IndexError) as exc:
                    last_exc = exc
                    logger.warning("AI request attempt %s failed: %s", attempt + 1, exc)
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    break
        raise AIError("AI service is temporarily unavailable. Please try again.") from last_exc

    async def ask(self, system: str, user: str, **kwargs) -> str:
        return await self.complete(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            **kwargs,
        )
