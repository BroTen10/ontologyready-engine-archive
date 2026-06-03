import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
from app.config import settings
from app.database import close_pool


@pytest.fixture(scope="session")
def event_loop_policy():
    if sys.platform == "win32":
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(autouse=True)
def set_api_key():
    settings.api_key = "test-key"


@pytest.fixture(autouse=True)
async def cleanup():
    from app.database import get_pool
    pool = await get_pool()
    await pool.execute("DELETE FROM ontology_links")
    await pool.execute("DELETE FROM ontology_objects")
    await pool.execute("DELETE FROM ontology_types")
    yield
    await close_pool()
