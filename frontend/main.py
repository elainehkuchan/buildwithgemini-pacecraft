"""FastAPI proxy for deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in browser).
The proxy authenticates with Application Default Credentials and forwards chat to
the deployed agent over the A2A protocol.
"""

import os
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest
from a2a.utils.constants import PROTOCOL_VERSION_1_0, VERSION_HEADER, TransportProtocol
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.protobuf.json_format import MessageToDict

# Load .env if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

RESOURCE = os.environ.get(
    "AGENT_ENGINE_RESOURCE_NAME",
    "projects/224009766543/locations/us-east1/reasoningEngines/873477325872693248",
)
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)

_A2UI_MIME = "application/json+a2ui"

_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        VERSION_HEADER: PROTOCOL_VERSION_1_0,
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


_contexts: dict[str, str] = {}


def _extract_parts(part: Part) -> list[dict]:
    out: list[dict] = []
    if part.text:
        out.append({"kind": "text", "text": part.text})
    elif part.url:
        out.append({"kind": "text", "text": part.url})
    elif part.HasField("data"):
        data_dict = MessageToDict(part.data)
        meta = dict(part.metadata) if part.metadata else {}
        mime = meta.get("mimeType")
        # Check if inside {"kind": "data", "data": ...} or direct A2UI object
        inner_data = data_dict.get("data", data_dict)
        if mime == _A2UI_MIME or "beginRendering" in inner_data or "surfaceUpdate" in inner_data:
            out.append({"kind": "a2ui", "data": inner_data})
        else:
            out.append({"kind": "text", "text": str(inner_data)})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as http_client:
        config = ClientConfig(
            httpx_client=http_client,
            supported_protocol_bindings=[
                TransportProtocol.JSONRPC,
                TransportProtocol.HTTP_JSON,
            ],
        )
        a2a_client = await create_client(A2A_BASE, config)

        context_id = _contexts.get(user_id, "")
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
            context_id=context_id,
        )

        async for chunk in a2a_client.send_message(SendMessageRequest(message=msg)):
            if chunk.HasField("artifact_update"):
                if chunk.artifact_update.context_id:
                    _contexts[user_id] = chunk.artifact_update.context_id
                for p in chunk.artifact_update.artifact.parts:
                    parts.extend(_extract_parts(p))
            elif chunk.HasField("task"):
                if chunk.task.context_id:
                    _contexts[user_id] = chunk.task.context_id
                for artifact in chunk.task.artifacts:
                    for p in artifact.parts:
                        parts.extend(_extract_parts(p))
            elif chunk.HasField("message"):
                if chunk.message.context_id:
                    _contexts[user_id] = chunk.message.context_id
                for p in chunk.message.parts:
                    parts.extend(_extract_parts(p))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
