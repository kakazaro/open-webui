from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict
import json
import uuid


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


# ── Conversion: Anthropic → OpenAI ─────────────────────────────

def convert_messages_to_chat(form_data: MessagesForm) -> dict:
    """Convert Anthropic /messages request to OpenAI /chat/completions format."""

    chat_messages = []

    # 1. System prompt → system message
    if form_data.system:
        if isinstance(form_data.system, str):
            system_text = form_data.system
        elif isinstance(form_data.system, list):
            system_text = "\n".join(
                block.get("text", "") for block in form_data.system
                if block.get("type") == "text"
            )
        else:
            system_text = str(form_data.system)

        chat_messages.append({"role": "system", "content": system_text})

    # 2. Convert each message
    for msg in form_data.messages:
        role = msg.get("role")
        content = msg.get("content")

        if isinstance(content, str):
            chat_messages.append({"role": role, "content": content})
            continue

        if isinstance(content, list):
            converted = _convert_content_blocks(role, content)
            chat_messages.extend(converted)

    # 3. Build chat completion payload
    chat_form = {
        "model": form_data.model,
        "messages": chat_messages,
        "max_tokens": form_data.max_tokens,
    }

    if form_data.stream is not None:
        chat_form["stream"] = form_data.stream
        if form_data.stream:
            chat_form["stream_options"] = {"include_usage": True}

    if form_data.temperature is not None:
        chat_form["temperature"] = form_data.temperature
    if form_data.top_p is not None:
        chat_form["top_p"] = form_data.top_p
    if form_data.stop_sequences is not None:
        chat_form["stop"] = form_data.stop_sequences

    # 4. Tools
    if form_data.tools:
        chat_form["tools"] = _convert_tools(form_data.tools)

    if form_data.tool_choice:
        chat_form["tool_choice"] = _convert_tool_choice(form_data.tool_choice)

    return chat_form


def _convert_content_blocks(role: str, blocks: list[dict]) -> list[dict]:
    """Convert Anthropic content blocks to OpenAI message(s)."""
    messages = []

    # Separate tool_result blocks (they become role="tool" in OpenAI)
    regular_parts = []
    for block in blocks:
        block_type = block.get("type")

        if block_type == "tool_result":
            # Flush any accumulated regular parts first
            if regular_parts:
                messages.append({"role": role, "content": regular_parts})
                regular_parts = []

            tool_content = block.get("content", "")
            if isinstance(tool_content, list):
                tool_content = "\n".join(
                    b.get("text", "") for b in tool_content
                    if b.get("type") == "text"
                )

            messages.append({
                "role": "tool",
                "tool_call_id": block.get("tool_use_id", ""),
                "content": str(tool_content),
            })

        elif block_type == "tool_use":
            # Assistant's tool call — accumulate as tool_calls
            if regular_parts:
                messages.append({"role": role, "content": regular_parts})
                regular_parts = []

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": block.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": block.get("name", ""),
                        "arguments": json.dumps(block.get("input", {})),
                    },
                }],
            })

        elif block_type == "text":
            regular_parts.append({
                "type": "text",
                "text": block.get("text", ""),
            })

        elif block_type == "image":
            source = block.get("source", {})
            if source.get("type") == "base64":
                url = f"data:{source.get('media_type', 'image/png')};base64,{source.get('data', '')}"
            else:
                url = source.get("url", "")
            regular_parts.append({
                "type": "image_url",
                "image_url": {"url": url},
            })

        elif block_type == "thinking":
            # Skip thinking blocks (not supported in OpenAI)
            pass

        else:
            # Fallback: treat as text
            regular_parts.append({
                "type": "text",
                "text": json.dumps(block),
            })

    if regular_parts:
        messages.append({"role": role, "content": regular_parts})

    return messages


def _convert_tools(tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool definitions to OpenAI format."""
    openai_tools = []
    for tool in tools:
        # Skip Anthropic built-in tools (computer, bash, text_editor)
        if "type" in tool and tool["type"] not in ("custom",):
            if tool.get("type") in (
                    "computer_20250124", "text_editor_20250124", "bash_20250124"
            ):
                continue

        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        })
    return openai_tools


def _convert_tool_choice(tool_choice: dict) -> Union[str, dict]:
    """Convert Anthropic tool_choice to OpenAI format."""
    tc_type = tool_choice.get("type", "auto")

    if tc_type == "auto":
        return "auto"
    elif tc_type == "any":
        return "required"
    elif tc_type == "none":
        return "none"
    elif tc_type == "tool":
        return {
            "type": "function",
            "function": {"name": tool_choice.get("name", "")},
        }
    return "auto"


# ── Conversion: OpenAI Response → Anthropic ────────────────────

def convert_chat_response_to_messages(chat_response: dict, model: str) -> dict:
    """Convert OpenAI /chat/completions response to Anthropic /messages format."""

    choice = chat_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    finish_reason = choice.get("finish_reason", "stop")

    # Map finish_reason → stop_reason
    stop_reason_map = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "content_filter": "end_turn",
    }
    stop_reason = stop_reason_map.get(finish_reason, "end_turn")

    # Build content blocks
    content = []

    if message.get("content"):
        content.append({
            "type": "text",
            "text": message["content"],
        })

    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            func = tc.get("function", {})
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}

            content.append({
                "type": "tool_use",
                "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
                "name": func.get("name", ""),
                "input": arguments,
            })
        stop_reason = "tool_use"

    if not content:
        content.append({"type": "text", "text": ""})

    # Build usage
    usage_data = chat_response.get("usage", {})
    usage = {
        "input_tokens": usage_data.get("prompt_tokens", 0),
        "output_tokens": usage_data.get("completion_tokens", 0),
    }

    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": model,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": usage,
    }


# ── Streaming Conversion ───────────────────────────────────────

async def convert_streaming_response(chat_stream_generator, model: str, max_tokens: int):
    """
    Wrap an OpenAI SSE stream and re-emit as Anthropic SSE events.
    """

    msg_id = f"msg_{uuid.uuid4().hex[:24]}"
    input_tokens = 0

    # message_start
    yield _sse("message_start", {
        "type": "message_start",
        "message": {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model,
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": 0,
            },
        },
    })

    # ping
    yield _sse("ping", {"type": "ping"})

    content_block_index = 0
    content_block_started = False
    current_tool_call_id = None
    current_tool_name = None
    output_tokens = 0
    stop_reason = "end_turn"

    async for chunk_raw in chat_stream_generator:
        # Parse the SSE chunk — handle both raw SSE strings and dict
        chunk = _parse_chunk(chunk_raw)
        if chunk is None:
            continue

        # Handle usage in final chunk
        if chunk.get("usage"):
            input_tokens = chunk["usage"].get("prompt_tokens", input_tokens)
            output_tokens = chunk["usage"].get("completion_tokens", output_tokens)

        choices = chunk.get("choices", [])
        if not choices:
            continue

        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")

        # Text content
        if delta.get("content") is not None:
            if not content_block_started:
                yield _sse("content_block_start", {
                    "type": "content_block_start",
                    "index": content_block_index,
                    "content_block": {"type": "text", "text": ""},
                })
                content_block_started = True

            yield _sse("content_block_delta", {
                "type": "content_block_delta",
                "index": content_block_index,
                "delta": {
                    "type": "text_delta",
                    "text": delta["content"],
                },
            })

        # Tool calls
        if delta.get("tool_calls"):
            for tc in delta["tool_calls"]:
                func = tc.get("function", {})

                # New tool call starts
                if func.get("name"):
                    # Close previous block if open
                    if content_block_started:
                        yield _sse("content_block_stop", {
                            "type": "content_block_stop",
                            "index": content_block_index,
                        })
                        content_block_index += 1

                    current_tool_call_id = tc.get(
                        "id", f"toolu_{uuid.uuid4().hex[:24]}"
                    )
                    current_tool_name = func["name"]

                    yield _sse("content_block_start", {
                        "type": "content_block_start",
                        "index": content_block_index,
                        "content_block": {
                            "type": "tool_use",
                            "id": current_tool_call_id,
                            "name": current_tool_name,
                            "input": {},
                        },
                    })
                    content_block_started = True

                # Argument deltas
                if func.get("arguments"):
                    yield _sse("content_block_delta", {
                        "type": "content_block_delta",
                        "index": content_block_index,
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": func["arguments"],
                        },
                    })

        # Finish
        if finish_reason:
            reason_map = {
                "stop": "end_turn",
                "length": "max_tokens",
                "tool_calls": "tool_use",
                "content_filter": "end_turn",
            }
            stop_reason = reason_map.get(finish_reason, "end_turn")

    # Close last content block
    if content_block_started:
        yield _sse("content_block_stop", {
            "type": "content_block_stop",
            "index": content_block_index,
        })

    # message_delta
    yield _sse("message_delta", {
        "type": "message_delta",
        "delta": {
            "stop_reason": stop_reason,
            "stop_sequence": None,
        },
        "usage": {
            "output_tokens": output_tokens,
        },
    })

    # message_stop
    yield _sse("message_stop", {"type": "message_stop"})


def _sse(event: str, data: dict) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _parse_chunk(chunk_raw) -> Optional[dict]:
    """Parse an SSE chunk into a dict."""
    if isinstance(chunk_raw, dict):
        return chunk_raw

    if isinstance(chunk_raw, (str, bytes)):
        text = chunk_raw if isinstance(chunk_raw, str) else chunk_raw.decode("utf-8")
        # Strip SSE prefix
        for line in text.strip().split("\n"):
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    return None
                try:
                    return json.loads(data_str)
                except json.JSONDecodeError:
                    return None
    return None


# ── Auth Header Conversion ──────────────────────────────────────

def extract_api_key_from_anthropic_headers(request: Request) -> Optional[str]:
    """
    Extract API key from Anthropic-style headers and normalize.
    Anthropic uses `x-api-key` header; OpenAI uses `Authorization: Bearer <key>`.
    """
    # Try Anthropic header first
    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key

    # Fallback to Bearer token
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]

    return None


# ── Main Handler ────────────────────────────────────────────────

async def messages_handler(
        request: Request,
        form_data: MessagesForm,
        x_api_key: Optional[str],
        authorization: Optional[str],
        user,
        chat_completion,
):
    """
    Handler for Anthropic /v1/messages endpoint.
    Converts to /chat/completions format, calls existing handler,
    then converts the response back.
    """

    # 0. convert header
    if x_api_key and not authorization:
        request.headers.__dict__["_list"] = [
                                                (k, v) for k, v in request.headers.__dict__["_list"]
                                                if k != b"x-api-key"
                                            ] + [(b"authorization", f"Bearer {x_api_key}".encode())]

    # 1. Convert request: Anthropic → OpenAI
    chat_form = convert_messages_to_chat(form_data)

    # 2. Call existing chat/completion handler
    response = await chat_completion(
        request=request,
        form_data=chat_form,
        user=user,
    )

    # 3. Convert response: OpenAI → Anthropic
    if form_data.stream:
        # Streaming: wrap the SSE generator
        if isinstance(response, StreamingResponse):
            return StreamingResponse(
                convert_streaming_response(
                    response.body_iterator,
                    model=form_data.model,
                    max_tokens=form_data.max_tokens,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

    # Non-streaming: convert JSON response
    if isinstance(response, JSONResponse):
        chat_data = json.loads(response.body.decode("utf-8"))
    elif isinstance(response, dict):
        chat_data = response
    else:
        chat_data = response

    messages_response = convert_chat_response_to_messages(
        chat_data, model=form_data.model
    )

    return JSONResponse(content=messages_response)
