"""Image generation tool for PaceCraft gear and route concepts."""

import uuid
from typing import Any, Dict
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded constants as required
PROJECT_ID = "qwiklabs-gcp-04-e75d23b408af"
LOCATION = "global"
MODEL_NAME = "gemini-3.1-flash-lite-image"
BUCKET_NAME = "pacecraft-gear-catalog-qwiklabs-gcp-04-e75d23b408af"


async def generate_gear_image(
    prompt: str,
    item_name: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generate a photo or visual concept for running shoes, gear, or race badges.

    Args:
        prompt: Descriptive prompt for image generation (e.g. 'A sleek studio product photo of a crimson red carbon-plated marathon racing shoe').
        item_name: Short name of the item or concept for the artifact filename (e.g. 'vaporfly_crimson_edition').
        tool_context: ADK ToolContext injected by the framework.

    Returns:
        A dictionary with the public image URL, artifact filename, and status.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    response = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from the model."}

    # 1. Save artifact for ADK Playground Artifacts panel
    clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in item_name.lower().strip())
    ext = "jpg" if "jpeg" in mime_type or "jpg" in mime_type else "png"
    filename = f"{clean_name}_{uuid.uuid4().hex[:6]}.{ext}"

    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public GCS bucket (no local disk write)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "item_name": item_name,
        "artifact_filename": filename,
        "image_url": public_url,
    }
