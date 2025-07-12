from acp_sdk.models import Message
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

from typing import List

from agentic_protocols.utils import Agent, AgentInvocator

from loguru import logger

class ACPAgentCaller:
    def __init__(self):        
        self.agent_to_invoke = Agent(name="alice", host="localhost", port=8333) 

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


class ACPAgentCallerExecutor(AgentExecutor):
    """Reimbursement AgentExecutor Example."""

    def __init__(self):
        self.agent = ACPAgentCaller()
        
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        logger.info(f"Query: {query}")
        try:
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
        id='fran',
        name='Fran Agent',
        description='contacts ACP agent Alice',
        tags=['a2a', 'bridte'],
        examples=['hi', 'hello world'],
    )


    # This will be the public-facing agent card
    public_agent_card = AgentCard(
        name='Fran Agent',
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
