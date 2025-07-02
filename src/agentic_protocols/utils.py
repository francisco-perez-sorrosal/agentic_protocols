from typing import List
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
from loguru import logger
from pydantic_settings import BaseSettings
from pydantic import Field


class Agent(BaseSettings):
    name: str
    host: str = "localhost"
    port: int = 8000

    def server(self):
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
    def __init__(self, server_url: str):
        self.server_url = server_url
    
    async def invoke(self, agent_name: str, msg="Howdy to echo from client!!", msg_type="text/plain") -> List[Message]:
        async with Client(base_url=self.server_url) as acp_client:
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
