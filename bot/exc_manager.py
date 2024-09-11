from __future__ import annotations

import asyncio
import datetime
import logging
import platform
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import discord

import config
from utils import const

if TYPE_CHECKING:
    from collections.abc import Generator

    from .bot import IrenesBot


log = logging.getLogger("exc_manager")


class ExceptionManager:
    """Exception Manager that."""

    __slots__: tuple[str, ...] = (
        "bot",
        "cooldown",
        "errors_cache",
        "_lock",
        "_most_recent",
        "error_webhook",
    )

    def __init__(self, bot: IrenesBot, *, cooldown: datetime.timedelta = datetime.timedelta(seconds=5)) -> None:
        self.bot: IrenesBot = bot
        self.cooldown: datetime.timedelta = cooldown

        self._lock: asyncio.Lock = asyncio.Lock()
        self._most_recent: datetime.datetime | None = None

        self.error_webhook: discord.Webhook = discord.Webhook.from_url(
            url=config.ERROR_HANDLER_WEBHOOK, session=self.bot.session
        )

    def _yield_code_chunks(self, iterable: str, *, chunks_size: int = 2000) -> Generator[str, None, None]:
        codeblocks: str = "```py\n{}```"
        max_chars_in_code = chunks_size - (len(codeblocks) - 2)  # chunks_size minus code blocker size

        for i in range(0, len(iterable), max_chars_in_code):
            yield codeblocks.format(iterable[i : i + max_chars_in_code])

    async def register_error(self, error: BaseException, embed: discord.Embed, *, mention: bool = True) -> None:
        """Register, analyse error and put it into queue to send to developers."""
        log.error("%s: `%s`.", error.__class__.__name__, embed.footer.text, exc_info=error)

        traceback_string = "".join(traceback.format_exception(error)).replace(str(Path.cwd()), "IrenesBot")

        async with self._lock:
            if self._most_recent and (delta := datetime.datetime.now(datetime.UTC) - self._most_recent) < self.cooldown:
                # We have to wait
                total_seconds = delta.total_seconds()
                log.debug("Waiting %s seconds to send the error.", total_seconds)
                await asyncio.sleep(total_seconds)

            self._most_recent = datetime.datetime.now(datetime.UTC)
            await self.send_error(traceback_string, embed, mention)

    async def send_error(self, traceback: str, embed: discord.Embed, mention: bool) -> None:
        """Send an error to the webhook.

        It is not recommended to call this yourself, call `register_error` instead.
        """
        if platform.system() == "Windows":
            return

        code_chunks = list(self._yield_code_chunks(traceback))

        if mention:
            await self.error_webhook.send(const.ERROR_ROLE_MENTION)

        for chunk in code_chunks:
            await self.error_webhook.send(chunk)

        if mention:
            await self.error_webhook.send(embed=embed)
