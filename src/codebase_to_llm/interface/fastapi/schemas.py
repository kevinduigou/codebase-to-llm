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
    target_language: str = "English"
    number_of_key_insights: int = 5


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


class VideoAddSubtitleRequest(BaseModel):
    file_id: str
    origin_language: str = "en"
    target_language: str = "en"
    output_filename: str = "subtitled.mkv"
    subtitle_color: str = "white"
    subtitle_style: str = "outline"  # "outline" or "boxed"
    use_soft_subtitles: bool = True
    subtitle_format: str = "ass"  # "mov_text" or "ass" for soft subtitles
    font_size_percentage: float = 4.0  # Font size as percentage of video height
    margin_percentage: float = 5.0  # Margins as percentage of video dimensions


class TaskStatusResponse(BaseModel):
    status: str
    file_id: str | None = None
    subtitle_file_id: str | None = None


class VideoSubtitleCreateRequest(BaseModel):
    video_file_id: str
    subtitle_file_id: str


class VideoSubtitleUpdateRequest(BaseModel):
    subtitle_file_id: str


class VideoSubtitleResponse(BaseModel):
    id: str
    video_file_id: str
    subtitle_file_id: str


class BurnAssRequest(BaseModel):
    output_filename: str


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
    target_language: str = "English"


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


class AssFileResponse(BaseModel):
    subtitle_file_id: str
    content: str


class AssFileUpdateRequest(BaseModel):
    content: str

    @classmethod
    def validate_ass_content(cls, content: str) -> str:
        """Validate ASS subtitle content format"""
        if not content or not content.strip():
            raise ValueError("ASS content cannot be empty")

        # Check for required ASS sections
        required_sections = ["[Script Info]", "[V4+ Styles]", "[Events]"]
        for section in required_sections:
            if section not in content:
                raise ValueError(f"Missing required ASS section: {section}")

        # Basic format validation
        lines = content.strip().split("\n")
        if len(lines) < 10:  # Minimum lines for a valid ASS file
            raise ValueError("ASS content appears to be too short or malformed")

        # Check for at least one dialogue line
        has_dialogue = any(line.strip().startswith("Dialogue:") for line in lines)
        if not has_dialogue:
            raise ValueError("ASS content must contain at least one Dialogue line")

        return content

    def __init__(self, **data):
        if "content" in data:
            data["content"] = self.validate_ass_content(data["content"])
        super().__init__(**data)
