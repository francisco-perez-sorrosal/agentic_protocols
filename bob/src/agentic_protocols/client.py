import asyncio
import os
from typing import List

from acp_sdk.models import Message
import click

from loguru import logger
from agentic_protocols.utils import AgentInvocator


async def main(host: str, port: int, agent_name, msg: str):
    server_url = f"http://{host}:{port}"
    logger.info(f"🚀 Agent Client contacting agent {agent_name} in {server_url}")
    
    client = AgentInvocator(server_url)
    response: List[Message] = await client.invoke(agent_name, msg)
    
    for msg in response:
        sender_agent = msg.role
        for part in msg.parts:
            if part.content_type == "text/plain":
                logger.info(f"[[{sender_agent}]] response:\n\n{part.content}")



@click.command()
@click.option("--host", default="localhost", help="Host")
@click.option("--port", default=os.environ.get("PORT", 8000), help="Port to listen on")
@click.option("--agent_name", default="alice", help="Agent name to call")
@click.option("--msg", default="Hey Alice, could you get me the CV from Francisco", help="Message to send to the agent")
def cli(host: str, port: int, agent_name: str, msg: str):
    """CLI entry point for uv script."""
    asyncio.run(main(host, port, agent_name, msg))


if __name__ == "__main__":
    cli()