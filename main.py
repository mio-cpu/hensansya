import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332

joined_members_introductions = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot or before.channel == after.channel:
        return

    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    if before.channel is None and after.channel is not None:
        introduction = None
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                introduction = message.content
                break
        joined_members_introductions[member] = introduction if introduction else "自己紹介が見つかりませんでした。"

    elif before.channel is not None and after.channel is None:
        joined_members_introductions.pop(member, None)

    if after.channel:
        for m, intro in joined_members_introductions.items():
            embed = discord.Embed(title=f"{m.display_name}さんの自己紹介", description=intro, color=discord.Color.blue())
            embed.set_thumbnail(url=m.avatar.url)
            await after.channel.send(embed=embed)

bot.run(TOKEN)
