import discord
from discord.ext import commands

class AnonymousMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.anonymous_channel_id = 123456789012345678  # 目安箱のチャンネルID

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != self.anonymous_channel_id or message.author.bot:
            return

        await message.delete()

        embed = discord.Embed(
            title="匿名メッセージ",
            description=message.content,
            color=discord.Color.blurple()
        )
        embed.set_footer(text="目安箱より")
        await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AnonymousMessages(bot))
