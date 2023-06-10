"""Command handlers for telegram command updates. It is responsible for parsing
updates and executing core module functionality."""

import abc
import inspect
import textwrap

import telegram
import telegram.ext as telegram_extensions

import bot.models
import database
from bot import formatter, utils
from chatgpt import memory

_default_context = telegram_extensions.ContextTypes.DEFAULT_TYPE


class Command(abc.ABC):
    """Base class for bot commands. All commands inherit from this class."""

    names: tuple[str]
    """The names that trigger the command. The first is the primary name."""
    description: str
    """The command's description."""
    filters: telegram_extensions.filters.BaseFilter | None = None
    """The command update filters."""
    block: bool | None = None
    """Whether the command should block other handlers."""
    group: int = 0
    """The command group. Commands in the same group are mutually exclusive.
    Lower group numbers have higher priority."""

    @property
    def handler(self) -> telegram_extensions.CommandHandler:
        """The command handler."""
        handler = telegram_extensions.CommandHandler(
            self.names,
            self.callback,
            filters=self.filters,
        )  # FIXME: add block to constructor
        handler.block = handler.block if self.block is None else self.block
        return handler

    @property
    def bot_command(self) -> telegram.BotCommand:
        return telegram.BotCommand(self.names[0], self.description)

    @staticmethod
    @abc.abstractmethod
    async def callback(update: telegram.Update, context: _default_context):
        """The callback function for the command."""
        pass


class HelpCommand(Command):
    names = ("start", "help")
    description = "Show the help message"

    help_message = textwrap.dedent(
        """
        The bot takes into context all messages sent in the chat, responding \
        only to messages that mention it.
        Set the system prompt by replying to a message with the command:
        ```
        /edit_sys@{bot}
        ```
        The text of the message to which you reply will be used as the prompt.
        You can also pass the text of the prompt directly to the command:
        ```
        /edit_sys@{bot} <prompt>
        ```
        """
    ).strip()

    @staticmethod
    async def callback(update, context):
        dummy_message = formatter.md_html(HelpCommand.help_message)
        dummy_message = dummy_message.format(bot=context.bot.username)
        await update.effective_chat.send_message(
            dummy_message, parse_mode=telegram.constants.ParseMode.HTML
        )


class UsageCommand(Command):
    names = ("usage",)
    description = "Show the user and chat usage"

    @staticmethod
    async def callback(update: telegram.Update, context: _default_context):
        update_message = update.effective_message
        message = bot.models.TextMessage(update_message)
        db_user = database.models.User(message.user.id).load()
        db_chat = database.models.Chat(message.chat.id).load()

        usage = (
            f"User usage: ${round(db_user.usage, 4)}\n"
            f"    tokens: {db_user.token_usage}\n"
            f"Chat usage: ${round(db_chat.usage, 4)}\n"
            f"    tokens: {db_chat.token_usage}"
        )
        await utils.reply_code(update_message, usage)


class DeleteHistoryCommand(Command):
    names = ("delete_history", "delete")
    description = "Delete the chat history"

    @staticmethod
    async def callback(update: telegram.Update, context: _default_context):
        update_message = update.effective_message
        message = bot.models.TextMessage(update_message)

        memory.ChatMemory.delete(database.url, message.session)
        await utils.reply_code(update_message, "Chat history deleted")


class PromptCommand(Command):
    names = ("edit_sys", "edit")
    description = "Edit the system prompt"

    @staticmethod
    async def callback(update: telegram.Update, context: _default_context):
        update_message = update.effective_message
        message = bot.models.TextMessage(update_message)

        sys_message = None
        try:  # parse the message in the format `/command content`
            sys_message = message.text.split(" ", 1)[1].strip()
        except IndexError:
            pass

        # parse text from reply if no text was found in message
        if not sys_message and message.reply:
            sys_message = message.reply.text
        if not sys_message:
            raise ValueError("No text found in message or reply")

        # create new system message
        utils.save_prompt(message.chat.id, message.topic_id, sys_message)
        await utils.reply_code(
            update_message, f"System prompt edited successfully"
        )


class GetSystemPrompt(Command):
    names = ("get_sys", "sys")
    description = "Get the system prompt"

    @staticmethod
    async def callback(update: telegram.Update, context: _default_context):
        update_message = update.effective_message
        message = bot.models.TextMessage(update_message)

        text = (
            utils.load_prompt(message.chat.id, message.topic_id)
            or "No system prompt found"
        )
        await utils.reply_code(update_message, text)


def all_commands(command=Command):
    """All available bot commands. Recursively yields all concrete subclasses
    of the base class."""
    if not inspect.isabstract(command):
        yield command()
    for subcommand in command.__subclasses__():
        yield from all_commands(subcommand)
