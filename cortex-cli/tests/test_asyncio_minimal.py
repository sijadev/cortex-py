import pytest
import asyncio

@pytest.mark.asyncio
async def test_asyncio_minimal():
    await asyncio.sleep(0.01)
    assert True
