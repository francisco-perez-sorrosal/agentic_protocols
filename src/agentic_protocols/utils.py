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
    port: int = 8333  # BeeAI Platform default port

    def server(self):
        # From inside the platform, the PLATFORM_URL env var is already setup, from clients outside use http://localhost:8333
        return f"{os.getenv('PLATFORM_URL', f'http://{self.host}:{self.port}').rstrip('/')}/api/v1/acp"


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
    
    async def invoke(self, msg="Howdy to echo from client!!", msg_type="text/plain") -> List[Message]:
        logger.info(f"Contacting agent {self.agent.name} through Base URL: {self.agent.server()}") 
        async with Client(base_url=self.agent.server()) as acp_client:
            logger.info(f"[[client]] sending message: {msg}")
            run = await acp_client.run_sync(
                agent=self.agent.name,
                input=[
                    Message(
                        parts=[MessagePart(content=msg, content_type=msg_type)]
                    )
                ],
            )
            
            return run.output
