"""Real integration tests for LLM (OpenRouter)."""

import os

import pytest
from dotenv import load_dotenv

from deepcode_vsa.config.settings import LLMSettings, ModelTier
from deepcode_vsa.llm.openrouter import OpenRouterClient

# Load env vars from .env file if it exists
load_dotenv()

@pytest.fixture
def real_settings():
    """Get settings with real credentials."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or "sk-or-v1" not in api_key:
        pytest.skip("OPENROUTER_API_KEY not found in .env or invalid")

    return LLMSettings(
        api_key=api_key,
        # Use cheap models for testing to save credits
        fast_model="meta-llama/llama-3.3-70b-instruct",
        default_tier=ModelTier.FAST
    )


@pytest.mark.asyncio
async def test_llm_connection_real(real_settings):
    """Test real connection to OpenRouter."""
    client = OpenRouterClient(real_settings)

    messages = [
        {"role": "user", "content": "Return exactly the word 'PONG'"}
    ]

    response = await client.chat(messages, tier=ModelTier.FAST)

    assert response is not None
    assert "choices" in response
    content = response["choices"][0]["message"]["content"]
    assert "PONG" in content.upper()


@pytest.mark.asyncio
async def test_llm_streaming_real(real_settings):
    """Test real streaming from OpenRouter."""
    client = OpenRouterClient(real_settings)

    messages = [
        {"role": "user", "content": "Count from 1 to 5. Output only the numbers."}
    ]

    chunks = []
    async for chunk in client.stream_chat(messages, tier=ModelTier.FAST):
        chunks.append(chunk)
        print(f"Chunk received: {chunk}")

    full_text = "".join(chunks)
    assert len(full_text) > 0
    # Check for at least some numbers
    assert any(c.isdigit() for c in full_text)
