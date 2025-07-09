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
from agentic_protocols.utils import Agent, AgentInvocator
    

def run_agent(this_agent: Agent):

    logger.info(f"{this_agent.name} Agent Settings: {this_agent}")

    server = Server()

    @server.agent(name=this_agent.name, metadata=Metadata(
        annotations=Annotations(
            
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                display_name=f"{this_agent.name} Agent",
                user_greeting=f"A proxy agent to {this_agent.contact.name}",
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
                logger.info(f"Contacting {this_agent.contact.server()} to get the CV")
                receiver_agent = this_agent.contact
                if not receiver_agent:
                    raise ValueError(f"{this_agent.name} has no agent to contact!!!")
                contact_client = AgentInvocator(receiver_agent)
                response = await contact_client.invoke( msg="Hey! Give me please the CV from Francisco")                
                
                cv = ""
                sender_agent_role = ""
                for msg in response:
                    sender_agent_role = msg.role
                    for part in msg.parts:
                        if part.content_type == "text/plain" and part.content is not None:
                            cv += part.content

                
                
                final_response = f"Here's Francisco's CV sent by [[{sender_agent_role}]]:\n\n{cv}"

        yield final_response
            
    # If server needs to be configured with URL, do it here
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)))



@click.command()
@click.option("--contact_to", default="bob", help="Agent to contact for CV")
def main(contact_to: str):
    """CLI entry point for uv script."""
    logger.info(f"🚀 Alice Agent will connect to {contact_to}, to ask it for Francisco's CV")
    agent_settings = Agent(name="alice", contact=Agent(name=contact_to))
    run_agent(agent_settings)

if __name__ == "__main__":
    main()
