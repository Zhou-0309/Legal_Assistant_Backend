from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from app.api.deps import get_yuanqi_client, require_service_auth, resolve_user_id
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.schemas.common import ChatCompletionRequest, ChatCompletionResponse
from app.services.conversation import to_yuanqi_messages
from app.services.yuanqi_client import YuanqiClient, extract_assistant_text

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/chat/completions",
    dependencies=[Depends(require_service_auth)],
    response_model=None,
)
async def agent_chat_completions(
    body: ChatCompletionRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[YuanqiClient, Depends(get_yuanqi_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> ChatCompletionResponse | StreamingResponse:
    user_id = resolve_user_id(settings, authorization, body.user_id)
    assistant_id = settings.assistant_id_for("chat")
    try:
        yuanqi_messages = to_yuanqi_messages(body.messages)
    except ValueError as e:
        raise AppError("invalid_messages", str(e), status_code=400) from e

    if body.stream:

        async def stream_gen() -> bytes:
            resp = await client.chat_completions_stream(
                assistant_id=assistant_id,
                user_id=user_id,
                messages=yuanqi_messages,
                custom_variables=body.custom_variables,
            )
            async for chunk in YuanqiClient.iter_stream_bytes(resp):
                yield chunk

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
        custom_variables=body.custom_variables,
    )
    text = extract_assistant_text(data)
    return ChatCompletionResponse(
        id=data.get("id"),
        created=str(data.get("created")) if data.get("created") is not None else None,
        assistant_id=data.get("assistant_id"),
        content=text,
        raw=data if settings.debug else None,
    )
