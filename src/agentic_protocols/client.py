import asyncio
import os
from typing import Any, List
from uuid import uuid4

import httpx
from acp_sdk.models import Message
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)
from agentic_protocols.utils import Agent, AgentInvocator
import typer
from loguru import logger


async def main_acp(agent: Agent, msg: str):
    logger.info(f"🚀 (ACP) Invoker contacting agent {agent.name} in {agent.server()}")
    
    agent_client = AgentInvocator(agent)
    response: List[Message] = await agent_client.invoke(msg)
    
    for msg in response:
        sender_agent = msg.role
        for part in msg.parts:
            if part.content_type == "text/plain":
                logger.info(f"[[{sender_agent}]] response:\n\n{part.content}")


async def main_a2a(agent: Agent, msg: str):
    logger.info(f"🚀 I(A2A) nvoker contacting agent {agent.name} in {agent.server()}")
    
    # Card resolver
    base_url = f'http://{agent.host}:{agent.port}'

    async with httpx.AsyncClient(timeout=10) as httpx_client:
        
        PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
            # agent_card_path uses default, extended_agent_card_path also uses default
        )
        

        # Fetch Public Agent Card
        logger.info(f'Attempting to fetch public agent card from: {base_url}{PUBLIC_AGENT_CARD_PATH}')
        card: AgentCard = await resolver.get_agent_card()
        logger.info(f"Agent Card: {card.model_dump_json(indent=2, exclude_none=True)}")
        if card.supportsAuthenticatedExtendedCard:
            logger.info(f"Supports Authenticated Extended Card, but we're not gonna fetch it")
        else:
            logger.info(f"Doesn't Support Authenticated Extended Card")
            
            
        # Initialize Client            
        client = A2AClient(
            httpx_client=httpx_client, agent_card=card
        )
        logger.info('A2AClient initialized.')

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': msg}
                ],
                'messageId': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()), params=MessageSendParams(**send_message_payload)
        )

        response = await client.send_message(request)
        
        logger.info(response.model_dump(mode='json', exclude_none=True))


def cli(framework:str = "a2a", 
        host: str = "localhost", 
        port: int | None = None, 
        agent_name: str ="alice", 
        msg: str="Hey! Could you get me the CV from Francisco"):
    """CLI entry point for uv script."""
    
    if not port:
        match framework.lower():
            case "a2a":                
                port = 9999
            case "acp":
                port = 8333
            case _:
                port = 8333
    
    agent_to_invoke = Agent(name=agent_name, host=host, port=port)
    match framework.lower():
        case "a2a":
            asyncio.run(main_a2a(agent_to_invoke, msg))
        case "acp":
            asyncio.run(main_acp(agent_to_invoke, msg))


if __name__ == "__main__":
    typer.run(cli)
