from __future__ import annotations

import base64
from fastapi import APIRouter, Depends, HTTPException

from codebase_to_llm.application.ports import BurnAssSubtitlePort
from codebase_to_llm.application import uc_burn_ass_subtitle
from codebase_to_llm.domain.user import User
from .dependencies import get_burn_ass_port, get_current_user
from .schemas import BurnAssSubtitleRequest

router = APIRouter(prefix="/burn_ass", tags=["burn_ass"])


@router.post("/", summary="Burn ASS subtitle into MKV and convert to MP4")
def burn_subtitle(
    request: BurnAssSubtitleRequest,
    current_user: User = Depends(get_current_user),
    port: BurnAssSubtitlePort = Depends(get_burn_ass_port),
) -> dict[str, str]:
    video_bytes = base64.b64decode(request.video_content)
    subtitle_bytes = base64.b64decode(request.subtitle_content)
    result = uc_burn_ass_subtitle.execute(video_bytes, subtitle_bytes, port)
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err())
    output = result.ok()
    assert output is not None
    encoded = base64.b64encode(output).decode("utf-8")
    return {"content": encoded}
