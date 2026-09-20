"""Timing and token-usage helpers for the TypeSafe async client."""
import time
from dataclasses import dataclass
from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, SystemOneResponse


@dataclass
class RequestMetrics:
    latency_ms: float
    model: str
    request_id: str
    input_tokens: int | None
    output_tokens: int | None

    @property
    def total_tokens(self) -> int | None:
        if self.input_tokens is None or self.output_tokens is None:
            return None
        return self.input_tokens + self.output_tokens


def _build(response: SystemOneResponse, latency_ms: float) -> RequestMetrics:
    return RequestMetrics(
        latency_ms=latency_ms,
        model=response.model,
        request_id=response.request_id,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


async def timed_call(
    client: AsyncTypeSafeClient,
    state: Any,
    questions: dict,
    **kwargs: Any,
) -> tuple[SystemOneResponse, RequestMetrics]:
    t0 = time.perf_counter()
    response = await client.system_one(state=state, questions=questions, **kwargs)
    return response, _build(response, (time.perf_counter() - t0) * 1000)
