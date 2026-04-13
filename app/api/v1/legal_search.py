from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.api.deps import get_yuanqi_client, require_service_auth, resolve_user_id
from app.core.config import Settings, get_settings
from app.schemas.common import ChatCompletionResponse, ClauseSearchRequest
from app.services.conversation import build_user_message, merge_custom_variables
from app.services.yuanqi_client import YuanqiClient, extract_assistant_text

router = APIRouter(prefix="/legal", tags=["legal"])


@router.post(
    "/clauses/search",
    dependencies=[Depends(require_service_auth)],
)
async def clause_search(
    body: ClauseSearchRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated[YuanqiClient, Depends(get_yuanqi_client)],
    authorization: Annotated[str | None, Header()] = None,
) -> ChatCompletionResponse:
    user_id = resolve_user_id(settings, authorization, body.user_id)
    if settings.hunyuan_api_key:
        assistant_id = settings.hunyuan_assistant_id_for("clause_search")
        base_url = settings.hunyuan_base_url
        api_key = settings.hunyuan_api_key
    else:
        assistant_id = settings.assistant_id_for("clause_search")
        base_url = None
        api_key = None

    prompt = (
        "请根据用户问题进行法律条款检索与说明，尽量引用可核对来源；用户问题：\n"
        f"{body.query}"
    )
    messages = build_user_message(prompt)
    base_vars = {"clause_filters": body.filters} if body.filters else None
    custom = merge_custom_variables(base_vars, body.custom_variables)

    data = await client.chat_completions(
        assistant_id=assistant_id,
        user_id=user_id,
        messages=messages,
        stream=False,
        custom_variables=custom,
        base_url=base_url,
        api_key=api_key,
    )
    text = extract_assistant_text(data)
    return ChatCompletionResponse(
        id=data.get("id"),
        created=str(data.get("created")) if data.get("created") is not None else None,
        assistant_id=data.get("assistant_id"),
        content=text,
        raw=data if settings.debug else None,
    )
