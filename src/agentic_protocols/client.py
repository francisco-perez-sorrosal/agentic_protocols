import asyncio
import os
from typing import List

from acp_sdk.models import Message
import click

from loguru import logger
from agentic_protocols.utils import Agent, AgentInvocator


async def main(agent: Agent, msg: str):
    logger.info(f"🚀 Agent Client contacting agent {agent.name} in {agent.server()}")
    
    client = AgentInvocator(agent)
    response: List[Message] = await client.invoke(agent.name, msg)
    
    for msg in response:
        sender_agent = msg.role
        for part in msg.parts:
            if part.content_type == "text/plain":
                logger.info(f"[[{sender_agent}]] response:\n\n{part.content}")



@click.command()
@click.option("--host", default="localhost", help="Host")
@click.option("--port", default=os.environ.get("PORT", 8333), help="Port to listen on")
@click.option("--agent_name", default="alice", help="Agent name to call")
@click.option("--is_in_local_beeai", default=True, help="If the agent is in the bee platform")
@click.option("--msg", default="Hey Alice, could you get me the CV from CUCU", help="Message to send to the agent")
def cli(host: str, port: int, agent_name: str, is_in_local_beeai: bool, msg: str):
    """CLI entry point for uv script."""
    agent = Agent(name=agent_name, host=host, port=port, in_local_platform=is_in_local_beeai)
    asyncio.run(main(agent, msg))


if __name__ == "__main__":
    cli()