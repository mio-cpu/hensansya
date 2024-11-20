import discord
from discord.ext import commands

class AnonymousMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.anonymous_channel_id = 1308544883899764746  # 目安箱チャンネルのIDを設定

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != self.anonymous_channel_id or message.author.bot:
            return  # BOTや対象外のチャンネルのメッセージは無視

        await message.delete()  # 元のメッセージを削除

        embed = discord.Embed(
            title="匿名メッセージ",
            description=message.content,
            color=discord.Color.blurple()
        )
        embed.set_footer(text="目安箱より")
        await message.channel.send(embed=embed)  # 匿名メッセージとして送信

async def setup(bot):
    await bot.add_cog(AnonymousMessages(bot))
