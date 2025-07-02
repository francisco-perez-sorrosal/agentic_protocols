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

from agentic_protocols.utils import AgentSettings

    
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
                logger.error(f"Error calling tool get_cv\n\n{result.content[0].text}\n\n")
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
    async def bob(
        input: list[Message],
        context: Context
    ) -> AsyncGenerator[RunYield, RunYieldResume]:
        """Bob will retrieve the CV for Francisco from a Remote MCP server"""
        match agent_settings.transport:
            case "sse":
                logger.info("📡 Opening SSE transport connection...")
                async with sse_client(
                    url=agent_settings.mcp_server_url,
                    auth=None,
                    timeout=60,
                ) as (read_stream, write_stream):
                    cv_as_text = await _run_session(agent_settings.mcp_server_url, read_stream, write_stream, None)
            case 'streamable-http':
                logger.info("📡 Opening StreamableHTTP transport connection...")
                async with streamablehttp_client(
                    url=agent_settings.mcp_server_url,
                    auth=None,
                    timeout=timedelta(seconds=60),
                ) as (read_stream, write_stream, get_session_id):
                    cv_as_text = await _run_session(agent_settings.mcp_server_url, read_stream, write_stream, get_session_id)
            case _:
                raise ValueError(f"Non supported transport {agent_settings.transport}!!!")
        
        yield cv_as_text
            
    # If server needs to be configured with URL, do it here
    server.run(host="0.0.0.0", port=8001)



@click.command()
@click.option("--mcp_host", default="cv-ltib.onrender.com", help="MCP Host")
@click.option("--mcp_port", default=os.environ.get("PORT", 10000), help="MCP Port where the server is listening")
@click.option(
    "--transport",
    default=os.environ.get("TRANSPORT", "sse"),
    type=click.Choice(["sse", "streamable-http"]),
    help="Transport protocol to use ('sse' or 'streamable-http')",
)
def main(mcp_host: str, mcp_port: int, transport: Literal["sse", "streamable-http"]):
    """CLI entry point for uv script."""
    mcp_server_url = f"https://{mcp_host}" + ("/mcp" if transport == "streamable-http" else "/sse")
    logger.info(f"🚀 Agent CV will connect to MCP server {mcp_server_url} with ({transport})")
    agent_settings = AgentSettings(name="bob", contact=None, mcp_server_url=mcp_server_url, transport=transport)
    run_agent(agent_settings)

if __name__ == "__main__":
    main()
