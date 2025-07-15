from multiprocessing import Value
import os
from acp_sdk.client.client import Client
from acp_sdk.models import AgentManifest, AsyncIterator, Message
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    FilePart,
    FileWithBytes,
    InvalidParamsError,
    Part,
    Task,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    completed_task,
    new_artifact,
)
from a2a.utils.errors import ServerError

from typing import AsyncGenerator, List

from agentic_protocols.utils import Agent, AgentInvocator

from loguru import logger

class ACPAgentCaller:
    def __init__(self, agent_id = "alice"):
        self.agent_to_invoke = Agent(name=agent_id, host="localhost", port=8333) 

    async def invoke(self, query, session_id) -> str:
    
        # ACP Agent invocation
        logger.info(f"Agent to invoke: {self.agent_to_invoke}")
        agent_client = AgentInvocator(self.agent_to_invoke)
        response: List[Message] = await agent_client.invoke(query)
    
        result =""
        for msg in response:
            sender_agent = msg.role
            for part in msg.parts:
                if part.content_type == "text/plain":
                    result += f"[[{sender_agent}]] (session:{session_id}) - response:\n\n{part.content}"
                                
        return result


class ACPAgentFinder:
    def __init__(self):
        self.platform_url = os.getenv("PLATFORM_URL", "http://localhost:8333/api/v1/acp")
        logger.info(f"ACP Platform url: {self.platform_url}")

    async def get_agents(self) -> AsyncGenerator[AgentManifest, None]:
        try:
            async with Client(base_url=self.platform_url) as client:
                async for agent in client.agents():
                    yield agent
        except Exception as e:
            logger.error(f"Error in fetching agents: {e}")
            return

class ACPAgentCallerExecutor(AgentExecutor):
    """AgentExecutor Example."""

    def __init__(self):
        pass
        
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        # Get Agents in ACP platform
        logger.info("Creating Agent finder...")
        agent_finder = ACPAgentFinder()
        logger.info("ACP Agents...")
        available_agents = []
        async for agent_manifest in agent_finder.get_agents():
            logger.info(f"ACP Agent: {agent_manifest.name}")
            available_agents.append(agent_manifest.name)
            
        message_to_send = ""
        agent_to_find = "alice"
        if context.message:
            logger.info("Analyzing Message parts for extracting text and ACP agent to call...")
            for part in context.message.parts:
                match part.root.kind:
                    case 'text':
                        message_to_send = part.root.text
                    case 'data':
                        agent_to_find = part.root.data['acp_agent_id']
                    case _:
                        logger.info(f"Unknown agent data")
        
        if agent_to_find not in available_agents:
            raise ValueError(f"Agent {agent_to_find} not in {available_agents}")
        query = context.get_user_input() if message_to_send == "" else message_to_send
        logger.info(f"Sending message: {query}")
        try:
            self.agent = ACPAgentCaller(agent_id=agent_to_find)
            result = await self.agent.invoke(query, context.context_id)
            logger.info(f'Final Result:\n{result}')
            
            parts = [
                Part(root=TextPart(text=result)),
            ]
            
            logger.info(f"Parts: {parts}")
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            raise ServerError(
                error=ValueError(f"!!!!!!!!! Error invoking agent: {e}")
            ) from e
            
            
        await event_queue.enqueue_event(
            completed_task(
                context.task_id,
                context.context_id,
                [new_artifact(parts, f'cv_{context.task_id}')],
                [context.message],
            )
        )
        logger.info(f"Completed task: {context.task_id}")

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())

    def _validate_request(self, context: RequestContext) -> bool:
        return False



def main():
    skill = AgentSkill(
        id='bridging',
        name='Bridge',
        description='Bridge to contact ACP agents Alice or Bob',
        tags=['a2a', 'bridge'],
        examples=['alice', 'bob'],
    )


    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='Fran',
        description='A bridge agent to contact ACP Agents',
        url='http://localhost:9999/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],  # Only the basic skill for the public card
        supportsAuthenticatedExtendedCard=True,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ACPAgentCallerExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9999)
    
    
if __name__ == '__main__':
    main()
