"""OpenAI chat model implementation."""

import chatgpt.core
import chatgpt.events
import chatgpt.memory
import chatgpt.openai
import chatgpt.tools


class ChatModel(chatgpt.openai.OpenAIModel):
    """Class responsible for interacting with the OpenAI API."""

    def __init__(
        self,
        model: chatgpt.core.ModelConfig,
        memory: chatgpt.memory.ChatMemory,
        tools: list[chatgpt.tools.Tool] = [],
        handlers: list[chatgpt.events.ModelEvent] = [],
    ) -> None:
        super().__init__(model, tools, handlers)
        self.memory = memory
        """The memory of the model."""

    async def run(self, new_message: chatgpt.core.UserMessage):
        """Generate a response to a new message."""
        return await super().run(new_message)

    async def _run_model(self, new_message):
        self.memory.chat_history.add_message(new_message)
        reply = None

        while True:  # run until model replied or stopped
            # generate reply and add to memory
            reply = await self._generate_reply(self.memory.messages)
            if reply is not None:  # potentially partial reply was generated
                self.memory.chat_history.add_message(reply)

            # use tool if model is still running and has requested it
            if isinstance(reply, chatgpt.core.ToolUsage) and self._running:
                await self._use_tool(reply)
                continue  # send results to model
            break  # no tool used or model stopped

        # trigger events and return reply
        if isinstance(reply, chatgpt.core.ModelMessage):
            await self.events_manager.trigger_model_reply(reply)
        return reply

    async def _use_tool(self, usage: chatgpt.core.ToolUsage):
        # use tool as cancelable task
        await self.events_manager.trigger_tool_use(usage)
        results = await self._cancelable(self.tools_manager.use(usage))
        # add to memory if not cancelled
        if isinstance(results, chatgpt.core.ToolResult):
            await self.events_manager.trigger_tool_result(results)
            self.memory.chat_history.add_message(results)
        return results
