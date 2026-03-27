import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import get_settings
from app.main import create_app


@pytest.mark.asyncio
@respx.mock
async def test_api_key_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "only-secret")
    get_settings.cache_clear()
    import app.db.session as db_session

    if db_session._engine is not None:
        await db_session._engine.dispose()
    db_session._engine = None
    db_session.SessionLocal = None

    app = create_app()
    settings = get_settings()
    respx.post(settings.yuanqi_base_url).mock(
        return_value=Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )
    )
    from app.db.base import Base
    from app.db.session import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "x"}], "stream": False},
            )
            assert r.status_code == 401
            r2 = await client.post(
                "/api/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "x"}], "stream": False},
                headers={"X-API-Key": "only-secret"},
            )
            assert r2.status_code != 401
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
        db_session._engine = None
        db_session.SessionLocal = None
        monkeypatch.delenv("API_KEY", raising=False)
        get_settings.cache_clear()
