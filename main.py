import discord
from discord.ext import commands
import os
import traceback

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

TOKEN = os.getenv('DISCORD_TOKEN')
ANONYMOUS_CHANNEL_ID = 1308900602578735114  # 目安箱のチャンネルID

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.channel.id != ANONYMOUS_CHANNEL_ID or message.author.bot:
        return

    try:
        # 詳細ログ
        print(f"[DEBUG] Received message: '{message.content}' from {message.author} in {message.channel.name}")

        await message.delete()

        if not message.content or message.content.strip() == "":
            await message.channel.send("匿名メッセージが空のため、送信できません。", delete_after=10)
            return

        embed = discord.Embed(
            title="匿名メッセージ",
            description=message.content.strip(),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="目安箱より")

        await message.channel.send(embed=embed)

    except Exception as e:
        print(f"[ERROR] Exception occurred in on_message: {e}")
        traceback.print_exc()

bot.run(TOKEN)
