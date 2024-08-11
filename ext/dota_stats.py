from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.ext import commands

from bot import IrenesCog

if TYPE_CHECKING:
    from bot import IrenesBot


class DotaStats(IrenesCog):
    @commands.command()
    async def mmr(self, ctx: commands.Context) -> None:
        await ctx.send("Not implemented yet!")


def prepare(bot: IrenesBot) -> None:
    bot.add_cog(DotaStats(bot))