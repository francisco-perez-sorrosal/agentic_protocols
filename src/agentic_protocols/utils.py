import os

from typing import List
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from loguru import logger
from pydantic_settings import BaseSettings
from pydantic import Field


class Agent(BaseSettings):
    name: str
    host: str = "localhost"
    port: int = 8333
    in_local_platform: bool = False

    def server(self):
        if self.in_local_platform:
            return f"{os.getenv('PLATFORM_URL', 'http://localhost:8333').rstrip('/')}/api/v1/acp"
        else:
            return f"http://{self.host}:{self.port}" 


class AgentSettings(BaseSettings):
    name: str
    contact: Agent | None
    mcp_server_url: str = ""
    transport: str = ""
    model_config = BaseSettings.model_config.copy()
    model_config.update(env_file='.env', case_sensitive=False, extra="ignore")
    openai_api_key: str = Field(default="")
    open_router_api_key: str = Field(default="")


class AgentInvocator:
    def __init__(self, agent: Agent):
        self.agent = agent
    
    async def invoke(self, agent_name: str, msg="Howdy to echo from client!!", msg_type="text/plain") -> List[Message]:
        logger.info(f"Base URL: {self.agent.server()}")
        logger.info(f"Agent name to contact: {agent_name}")
        async with Client(base_url=self.agent.server()) as acp_client:
            logger.info(f"[[client]] sending message: {msg}")
            run = await acp_client.run_sync(
                agent=agent_name,
                input=[
                    Message(
                        parts=[MessagePart(content=msg, content_type=msg_type)]
                    )
                ],
            )
            
            return run.output
