"""法律对话 /agent/chat 与 /chat/completions 的共享实现（可选 session 落库）。"""

from __future__ import annotations

from typing import Any

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import resolve_user_id
from app.core.config import Settings
from app.core.exceptions import AppError
from app.schemas.common import ChatCompletionRequest, ChatCompletionResponse
from app.services import chat_history
from app.services.conversation import to_yuanqi_messages
from app.services.sse_text_accumulator import SSEAssistantTextAccumulator
from app.services.users import get_or_create_user
from app.services.yuanqi_client import YuanqiClient, extract_assistant_text


def _validate_session_new_messages(body: ChatCompletionRequest) -> None:
    for m in body.messages:
        if m.role != "user":
            raise AppError(
                "invalid_messages",
                "携带 session_id 时，messages 只能包含本轮新增的用户消息（role=user）",
                status_code=400,
            )


async def handle_yuanqi_chat_completion(
    *,
    body: ChatCompletionRequest,
    settings: Settings,
    client: YuanqiClient,
    db: AsyncSession,
    authorization: str | None,
) -> ChatCompletionResponse | StreamingResponse:
    user_id = resolve_user_id(settings, authorization, body.user_id)
    assistant_id = settings.assistant_id_for("chat")

    session_row: Any = None
    yuanqi_messages: list[dict[str, Any]]

    if body.session_id:
        user = await get_or_create_user(db, user_id, settings)
        _validate_session_new_messages(body)
        session_row = await chat_history.get_chat_session_owned(
            db, user.id, body.session_id
        )
        existing = await chat_history.load_messages_as_schemas(db, body.session_id)
        merged = chat_history.merge_for_yuanqi(existing, body.messages)
        try:
            yuanqi_messages = to_yuanqi_messages(merged)
        except ValueError as e:
            raise AppError("invalid_messages", str(e), status_code=400) from e
    else:
        try:
            yuanqi_messages = to_yuanqi_messages(body.messages)
        except ValueError as e:
            raise AppError("invalid_messages", str(e), status_code=400) from e

    custom_vars = body.custom_variables

    if body.stream:

        async def stream_gen() -> bytes:
            acc = SSEAssistantTextAccumulator()
            resp = None
            try:
                resp = await client.chat_completions_stream(
                    assistant_id=assistant_id,
                    user_id=user_id,
                    messages=yuanqi_messages,
                    custom_variables=custom_vars,
                )
                async for chunk in YuanqiClient.iter_stream_bytes(resp):
                    acc.feed(chunk)
                    yield chunk
            finally:
                if session_row is not None and resp is not None:
                    text = acc.get_text().strip() or None
                    await chat_history.persist_turn(
                        db,
                        session_row=session_row,
                        new_user_messages=body.messages,
                        assistant_text=text,
                    )

        return StreamingResponse(
            stream_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    data = await client.chat_completions(
        assistant_id=assistant_id,
        user_id=user_id,
        messages=yuanqi_messages,
        stream=False,
        custom_variables=custom_vars,
    )
    text = extract_assistant_text(data)
    if session_row is not None:
        await chat_history.persist_turn(
            db,
            session_row=session_row,
            new_user_messages=body.messages,
            assistant_text=text,
        )

    return ChatCompletionResponse(
        id=data.get("id"),
        created=str(data.get("created")) if data.get("created") is not None else None,
        assistant_id=data.get("assistant_id"),
        content=text,
        raw=data if settings.debug else None,
    )
