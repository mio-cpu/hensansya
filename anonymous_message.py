import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')
ANONYMOUS_CHANNEL_ID = 1308544883899764746  # 目安箱のチャンネルID

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # BOTが投稿したメッセージには反応しない

    if message.channel.id == ANONYMOUS_CHANNEL_ID:
        await message.delete()  # 投稿を削除して匿名性を保持
        anonymous_embed = discord.Embed(
            description=message.content,
            color=discord.Color.blue()
        )
        anonymous_embed.set_author(name="匿名", icon_url=bot.user.avatar.url)
        await message.channel.send(embed=anonymous_embed)

bot.run(TOKEN)

