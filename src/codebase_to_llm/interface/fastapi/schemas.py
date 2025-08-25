from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    user_name: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class AddApiKeyRequest(BaseModel):
    id_value: str
    url_provider: str
    api_key_value: str


class UpdateApiKeyRequest(BaseModel):
    api_key_id: str
    new_url_provider: str
    new_api_key_value: str


class AddModelRequest(BaseModel):
    id_value: str
    name: str
    api_key_id: str


class UpdateModelRequest(BaseModel):
    model_id: str
    new_name: str
    new_api_key_id: str


class AddFileRequest(BaseModel):
    path: str


class AddSnippetRequest(BaseModel):
    path: str
    start: int
    end: int
    text: str


class AddExternalSourceRequest(BaseModel):
    url: str
    include_timestamps: bool = False


class RemoveExternalSourceRequest(BaseModel):
    url: str


class RemoveElementsRequest(BaseModel):
    elements: list[str]


class AddPromptFromFileRequest(BaseModel):
    path: str


class ModifyPromptRequest(BaseModel):
    new_content: str


class SetPromptFromFavoriteRequest(BaseModel):
    content: str


class FavoritePromptCreateRequest(BaseModel):
    name: str
    content: str


class FavoritePromptUpdateRequest(BaseModel):
    id: str
    name: str
    content: str


class FavoritePromptIdRequest(BaseModel):
    id: str


class RuleCreateRequest(BaseModel):
    name: str
    content: str
    description: str | None = None
    enabled: bool = True


class RuleUpdateRequest(BaseModel):
    name: str
    content: str
    description: str | None = None
    enabled: bool = True


class RuleNameRequest(BaseModel):
    name: str


class AddFileAsPromptVariableRequest(BaseModel):
    variable_key: str
    relative_path: str


class AddRecentRepositoryPathRequest(BaseModel):
    path: str


class GenerateResponseRequest(BaseModel):
    model_id: str
    include_tree: bool = True
    root_directory_path: str | None = None


class TestMessageRequest(BaseModel):
    model_id: str
    message: str
    previous_response_id: Optional[str] = None
    stream_format: Literal["sse", "ndjson"] = "sse"


class ExtractKeyInsightsRequest(BaseModel):
    model_id: str
    video_url: str


class KeyInsightResponse(BaseModel):
    content: str
    video_url: str
    begin_timestamp: Timestamp
    end_timestamp: Timestamp


class KeyInsightsTaskStatusResponse(BaseModel):
    status: str
    insights: list[KeyInsightResponse] | None = None


class CopyContextRequest(BaseModel):
    include_tree: bool = True
    root_directory_path: str | None = None


class UploadFileRequest(BaseModel):
    name: str
    content: str
    directory_id: str | None = None


class UpdateFileRequest(BaseModel):
    new_name: str | None = None
    new_directory_id: str | None = None


class CreateDirectoryRequest(BaseModel):
    name: str
    parent_id: str | None = None


class UpdateDirectoryRequest(BaseModel):
    new_name: str | None = None
    new_parent_id: str | None = None


class YouTubeDownloadRequest(BaseModel):
    url: str
    start: str
    end: str
    name: str


class VideoTranslationRequest(BaseModel):
    file_id: str
    target_language: str = "en"
    output_filename: str = "translated.mp4"


class TaskStatusResponse(BaseModel):
    status: str
    file_id: str | None = None


class Timestamp(BaseModel):
    hour: int
    minute: int
    second: int


class KeyInsightRequest(BaseModel):
    content: str
    video_url: str
    begin_timestamp: Timestamp
    end_timestamp: Timestamp


class CreateVideoKeyInsightsRequest(BaseModel):
    title: str
    key_insights: list[KeyInsightRequest] | None = None


class UpdateVideoKeyInsightsRequest(BaseModel):
    title: str | None = None
    key_insights: list[KeyInsightRequest] | None = None


class VideoKeyInsightsResponse(BaseModel):
    id: str
    title: str
    key_insights: list[KeyInsightResponse]
    created_at: str
    updated_at: str


class ExtractSummaryRequest(BaseModel):
    model_id: str
    video_url: str


class SummarySegmentResponse(BaseModel):
    content: str
    video_url: str
    begin_timestamp: Timestamp
    end_timestamp: Timestamp


class SummaryTaskStatusResponse(BaseModel):
    status: str
    segments: list[SummarySegmentResponse] | None = None


class SummarySegmentRequest(BaseModel):
    content: str
    video_url: str
    begin_timestamp: Timestamp
    end_timestamp: Timestamp


class CreateVideoSummaryRequest(BaseModel):
    title: str
    segments: list[SummarySegmentRequest] | None = None


class UpdateVideoSummaryRequest(BaseModel):
    title: str | None = None
    segments: list[SummarySegmentRequest] | None = None


class VideoSummaryResponse(BaseModel):
    id: str
    title: str
    segments: list[SummarySegmentResponse]
    created_at: str
    updated_at: str
