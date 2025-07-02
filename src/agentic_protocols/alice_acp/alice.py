import asyncio
import os

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Literal

import click

from acp_sdk.models import Message
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from agentic_protocols.utils import Agent, AgentInvocator, AgentSettings
    
async def _run_session(server_url, read_stream, write_stream, get_session_id):
    """Run the MCP session with the given streams."""
    logger.info("🤝 Initializing MCP session...")
    async with ClientSession(read_stream, write_stream) as session:
        logger.info(f"⚡ Starting session initialization {session}...")
        await session.initialize()
        logger.info("✨ Session initialization complete!")

        logger.info(f"\n✅ Connected to MCP server at {server_url}")
        if get_session_id:
            session_id = get_session_id()
            if session_id:
                print(f"Session ID: {session_id}")

        result = await session.call_tool("get_cv", {})
        logger.info(f"\n🔧 'get_cv' result:")
        if hasattr(result, "content"):
            if result.isError:
                first_content = result.content[0] if result.content else None
                if (
                    first_content is not None
                    and getattr(first_content, 'type', None) == 'text'
                    and hasattr(first_content, 'text')
                ):
                    logger.error(f"Error calling tool get_cv\n\n{getattr(first_content, 'text', repr(first_content))}\n\n")
                else:
                    logger.error(f"Error calling tool get_cv\n\n{repr(first_content)}\n\n")
                return
                            
            for content in result.content:
                if content.type == "text":
                    return content.text
                else:
                    return f"Content wo text: {content}"
        else:
            return "Result with no content!\n\n{result}"


def run_agent(agent_settings: AgentSettings):

    logger.info(f"Settings: {agent_settings}")

    server = Server()

    @server.agent(name=agent_settings.name)
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
