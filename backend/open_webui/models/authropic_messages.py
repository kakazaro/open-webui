import aiohttp
import logging
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict
import json

from starlette.responses import PlainTextResponse

from open_webui.env import AIOHTTP_CLIENT_TIMEOUT, AIOHTTP_CLIENT_SESSION_SSL
from open_webui.routers.openai import get_all_models, get_headers_and_cookies
from open_webui.utils.misc import stream_wrapper, cleanup_response

log = logging.getLogger(__name__)


# ── Request Model ───────────────────────────────────────────────

class MessagesForm(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    max_tokens: int
    messages: list[dict]
    system: Optional[Union[str, list[dict]]] = None
    stream: Optional[bool] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[list[str]] = None
    tools: Optional[list[dict]] = None
    tool_choice: Optional[dict] = None
    thinking: Optional[dict] = None
    metadata: Optional[dict] = None

# ── Main Handler ────────────────────────────────────────────────

async def messages_handler(
        request: Request,
        form_data: MessagesForm,
        user,
):
    payload = form_data.model_dump(exclude_none=True)
    body = json.dumps(payload)

    idx = 0
    model_id = form_data.model
    if model_id:
        models = request.app.state.OPENAI_MODELS
        if not models or model_id not in models:
            await get_all_models(request, user=user)
            models = request.app.state.OPENAI_MODELS
        if model_id in models:
            idx = models[model_id]["urlIdx"]

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

        request_url = f"{url}/anthropic/v1/messages"
        session = aiohttp.ClientSession(
            trust_env=True,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT),
        )
        r = await session.request(
            method="POST",
            url=request_url,
            data=body,
            headers=headers,
            cookies=cookies,
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
                    return PlainTextResponse(
                        status_code=r.status, content=response_data
                    )

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
