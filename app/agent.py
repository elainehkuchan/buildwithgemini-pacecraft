# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from app.tools_firestore import add_or_update_shoe, get_shoe_details, list_shoes
from app.tools_image import generate_gear_image
from app.tools_pace import calculate_training_paces


MODEL = "gemini-3.8-flash"
SANDBOX_RESOURCE_NAME = "projects/224009766543/locations/us-east1/reasoningEngines/5683743940369448960/sandboxEnvironments/8233525698833154048"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
)

try:
    from app.a2ui_instruction import INSTRUCTION as instruction
except ImportError:
    try:
        from a2ui.basic_catalog.provider import BasicCatalog
        from a2ui.schema.manager import A2uiSchemaManager

        schema_manager = A2uiSchemaManager(
            version="0.8",
            catalogs=[BasicCatalog.get_config("0.8")],
        )
        instruction = schema_manager.generate_system_prompt(
            role_description=(
                "You are PaceCraft, an expert fitness and gear coach. You help runners "
                "and athletes find the best running shoes, analyze gear specifications, calculate training paces, "
                "and train effectively. You have access to a Firestore-backed running shoe catalog, a training pace calculator, "
                "an image generation tool, and a secure Python code execution sandbox.\n\n"
                "- Use your Python code sandbox to compute marathon splits, progressive pacing charts, or custom statistics.\n"
                "- Use calculate_training_paces when users ask about their training pace zones or mention their race times.\n"
                "- Use list_shoes, get_shoe_details, and add_or_update_shoe to inspect and manage gear recommendations.\n"
                "- Use generate_gear_image when the user wants to generate, design, or see an image of running gear, shoes, routes, or race badges."
            ),
            workflow_description="Analyze the request, call relevant tools, and return structured UI when appropriate.",
            ui_description=(
                "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
                "Never nest a Card inside a Card. "
                "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
                "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
                "nothing in adk web). "
                "You may include one Image component, but only when you have a public https "
                "URL for the image (for example the URL an image tool returns after uploading "
                "to a public bucket). Set the Image url to that exact https link, for example "
                "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
                "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
                "not have a public URL, add a short Text line noting the image instead. "
                "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
                "headings and emphasis. "
                "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
                "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
            ),
            include_schema=True,
            include_examples=True,
        )
    except Exception:
        instruction = (
            "You are PaceCraft, an expert fitness and gear coach. You help runners "
            "and athletes find the best running shoes, analyze gear specifications, calculate training paces, "
            "and train effectively. You have access to a Firestore-backed running shoe catalog, a training pace calculator, "
            "an image generation tool, and a secure Python code execution sandbox."
        )

from app.a2ui_utils import a2ui_callback

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        generate_gear_image,
        calculate_training_paces,
        list_shoes,
        get_shoe_details,
        add_or_update_shoe,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
