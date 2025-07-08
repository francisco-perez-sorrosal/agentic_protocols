import asyncio
import os
from typing import List

from acp_sdk.models import Message
import click

from loguru import logger
from agentic_protocols.utils import Agent, AgentInvocator


async def main(agent: Agent, msg: str):
    logger.info(f"🚀 Invoker contacting agent {agent.name} in {agent.server()}")
    
    agent_client = AgentInvocator(agent)
    response: List[Message] = await agent_client.invoke(msg)
    
    for msg in response:
        sender_agent = msg.role
        for part in msg.parts:
            if part.content_type == "text/plain":
                logger.info(f"[[{sender_agent}]] response:\n\n{part.content}")



@click.command()
@click.option("--host", default="localhost", help="Host")
@click.option("--port", default=os.environ.get("PORT", 8333), help="Port to listen on")
@click.option("--agent_name", default="alice", help="Agent name to call")
@click.option("--msg", default="Hey! Could you get me the CV from Francisco", help="Message to send to the agent")
def cli(host: str, port: int, agent_name: str, msg: str):
    """CLI entry point for uv script."""
    agent_to_invoke = Agent(name=agent_name, host=host, port=port)
    asyncio.run(main(agent_to_invoke, msg))


if __name__ == "__main__":
    cli()