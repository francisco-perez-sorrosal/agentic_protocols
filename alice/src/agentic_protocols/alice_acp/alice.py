import asyncio
import os

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Literal

from acp_sdk.models.platform import PlatformUIType
import click

from acp_sdk.models import Message, Metadata, PlatformUIAnnotation
from acp_sdk.models.models import Annotations, CitationMetadata
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from agentic_protocols.utils import Agent, AgentInvocator, AgentSettings
    

def run_agent(agent_settings: AgentSettings):

    logger.info(f"Settings: {agent_settings}")

    server = Server()

    @server.agent(name=agent_settings.name, metadata=Metadata(
        annotations=Annotations(
            
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                display_name="Alice Agent",
                user_greeting="A proxy agent to Bob",
                tools=[],
            )
        ),
    ))
    async def alice(
        input: list[Message],
        context: Context
    ) -> AsyncGenerator[RunYield, RunYieldResume]:
        """Alice will contact Bob for getting Francisco's CV!."""
        
        last_msg: Message = input[-1]
        logger.info(f"Last Mesage received: {last_msg}")
        
        final_response = "I'm sorry. I couldn't find nothing useful"
        for part in last_msg.parts:
            logger.info(f"Part: {part}")
            if part.content_type == 'text/plain' and part.content is not None and ("francisco" in part.content.lower()):
                logger.info(f"Contacting {agent_settings.contact.server()} to get the CV")
                contact_agent = agent_settings.contact
                client = AgentInvocator(contact_agent)
                response = await client.invoke(contact_agent.name, msg="Hey! Give me please the CV from Francisco")                
                
                cv = ""
                sender_agent = ""
                for msg in response:
                    sender_agent = msg.role
                    for part in msg.parts:
                        if part.content_type == "text/plain" and part.content is not None:
                            cv += part.content

                
                
                final_response = f"Here's Francisco's CV sent by [[{sender_agent}]]:\n\n{cv}"

        yield final_response
            
    # If server needs to be configured with URL, do it here
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))



@click.command()
@click.option("--contact_to", default="bob", help="Agent to contact for CV")
@click.option("--is_in_local_beeai", default=True, help="If the agent is in the bee platform")
def main(contact_to: str, is_in_local_beeai: bool):
    """CLI entry point for uv script."""
    platform_url = os.getenv("PLATFORM_URL", "no platform URL")
    logger.info(f"PLATFORM_URL={platform_url}")
    logger.info(f"🚀 Alice Agent will connect to {contact_to}, to ask it for Francisco's CV")
    agent_settings = AgentSettings(name="alice", contact=Agent(name=contact_to, in_local_platform=is_in_local_beeai))
    run_agent(agent_settings)

if __name__ == "__main__":
    main()
