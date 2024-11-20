import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332  # 自己紹介チャンネルID
ANONYMOUS_CHANNEL_NAME = "目安箱"  # 匿名メッセージ用チャンネル名
SECRET_ROLE_NAME = "秘密のロール"  # BOTが反応しないロール名


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    if after.channel and (before.channel != after.channel):
        if any(role.name == SECRET_ROLE_NAME for role in member.roles):
            return

        messages = []
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                messages.append(message)

        channel = after.channel
        await channel.purge(limit=100, check=lambda m: m.author == bot.user)

        if messages:
            for msg in messages:
                embed = discord.Embed(
                    title=f"{member.display_name}さんの自己紹介",
                    description=msg.content,
                    color=discord.Color.blue(),
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else "")
                await channel.send(embed=embed)
        else:
            await channel.send(
                f"{member.display_name}さんが入室しましたが、自己紹介が見つかりませんでした。"
            )


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if message.channel.name == ANONYMOUS_CHANNEL_NAME:
        await message.delete()
        await message.channel.send(f"匿名のメッセージ: {message.content}")

    await bot.process_commands(message)


bot.run(TOKEN)
