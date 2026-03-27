from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: Any = None


class MessagePart(BaseModel):
    type: str = "text"
    text: str | None = None
    image_url: dict[str, Any] | None = None


class ChatMessage(BaseModel):
    role: str
    content: str | list[MessagePart]


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    stream: bool = False
    user_id: str | None = None
    custom_variables: dict[str, str] | None = None


class ChatCompletionResponse(BaseModel):
    id: str | None = None
    created: str | None = None
    assistant_id: str | None = None
    content: str | None = None
    raw: dict[str, Any] | None = None
    contract_id: str | None = Field(None, description="合同生成落库后的 contracts.id")


class ClauseSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    filters: str | None = Field(None, description="可选检索范围/标签，如与元器 custom_variables 对齐")
    user_id: str | None = None
    custom_variables: dict[str, str] | None = None


class ContractGenerateRequest(BaseModel):
    contract_type: str = Field(..., min_length=1, max_length=256)
    parties: str | None = Field(None, max_length=4000)
    subject_matter: str | None = Field(None, max_length=8000)
    extra_requirements: str | None = Field(None, max_length=8000)
    user_id: str | None = None
    session_id: str | None = Field(None, description="可选，关联 chat_sessions.id")
    custom_variables: dict[str, str] | None = None


class ContractReviewResultResponse(BaseModel):
    contract_id: str
    status: str = Field(..., description="pending / done / failed")
    result: str | None = None
    error: str | None = None
