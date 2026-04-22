import aiohttp
import json
import logging
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.responses import PlainTextResponse

from open_webui.config import BYPASS_ADMIN_ACCESS_CONTROL
from open_webui.env import (
    AIOHTTP_CLIENT_TIMEOUT,
    AIOHTTP_CLIENT_SESSION_SSL,
    ENABLE_FORWARD_USER_INFO_HEADERS, BYPASS_MODEL_ACCESS_CONTROL,
)
from open_webui.routers.openai import get_headers_and_cookies
from open_webui.utils.headers import include_user_info_headers
from open_webui.utils.misc import stream_wrapper, cleanup_response, find_model_id_from_alias
from open_webui.utils.models import check_model_access, get_all_models

log = logging.getLogger(__name__)


# ── Request Model ──────────────────────────────────────────────────────────────

class GeminiForm(BaseModel):
    model_config = ConfigDict(extra="allow")

    contents: Optional[list[dict]] = None
    tools: Optional[list[dict]] = None
    safetySettings: Optional[list[dict]] = None
    generationConfig: Optional[dict] = None
    systemInstruction: Optional[dict] = None
    stream: Optional[bool] = None


# ── Main Handler ───────────────────────────────────────────────────────────────

async def gemini_api_handler(
        request: Request,
        model_id: str,
        action_id: str,
        form_data: GeminiForm,
        user,
):
    payload = form_data.model_dump(exclude_none=True)
    body = json.dumps(payload)

    idx = 0
    if model_id:
        models = request.app.state.OPENAI_MODELS
        if not models or model_id not in models:
            await get_all_models(request, user=user)
            models = request.app.state.OPENAI_MODELS

        # TODO renesas for model alias
        if model_id not in models:
            model_id2 = find_model_id_from_alias(model_id)
            if model_id2 in models:
                model_id = model_id2

        if model_id in models:
            idx = models[model_id]["urlIdx"]
        else:
            raise HTTPException(404, "Model not found")

        # Check if user has access to the model
        if not BYPASS_MODEL_ACCESS_CONTROL and (
                user.role != "admin" or not BYPASS_ADMIN_ACCESS_CONTROL
        ):
            try:
                await check_model_access(user, models[model_id])
            except Exception:
                raise HTTPException(404, "Model not found")

    # TODO renesas for logs model usage
    request.state.logs_model = model_id

    url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
    key = request.app.state.config.OPENAI_API_KEYS[idx]
    api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.OPENAI_API_CONFIGS.get(url, {}),  # Legacy support
    )

    r = None
    session = None
    streaming = False

    try:
        headers, cookies = await get_headers_and_cookies(
            request, url, key, api_config, user=user
        )

        request_url = f"{url}/gemini/v1beta/models/{model_id}:{action_id}"
        session = aiohttp.ClientSession(
            trust_env=True,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT),
        )
        r = await session.request(
            method="POST",
            url=request_url,
            data=body,
            headers=headers,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                stream_wrapper(r, session),
                status_code=r.status,
                headers=dict(r.headers),
            )
        else:
            try:
                response_data = await r.json()
            except Exception:
                response_data = await r.text()

            if r.status >= 400:
                if isinstance(response_data, (dict, list)):
                    return JSONResponse(status_code=r.status, content=response_data)
                else:
                    return PlainTextResponse(status_code=r.status, content=response_data)

            return response_data
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=r.status if r else 500,
            detail="Open WebUI: Server Connection Error",
        )
    finally:
        if not streaming:
            await cleanup_response(r, session)
