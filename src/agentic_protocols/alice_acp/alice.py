import asyncio
import os

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Literal

import click

from acp_sdk.models import Message, Metadata
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

    @server.agent(name=agent_settings.name, metadata=Metadata())
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
                client = AgentInvocator(agent_settings.contact.server())
                response = await client.invoke(agent_settings.contact.name, msg="Hey! Give me please the CV from Francisco")                
                
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
    server.run(host="0.0.0.0")



@click.command()
@click.option("--contact_to", default="bob", help="Agent to contact for CV")
def main(contact_to: str):
    """CLI entry point for uv script."""
    logger.info(f"🚀 Alice Agent will connect to {contact_to}, to ask it for Francisco's CV")
    agent_settings = AgentSettings(name="alice", contact=Agent(name="bob", host="0.0.0.0", port=8001))
    run_agent(agent_settings)

if __name__ == "__main__":
    main()
