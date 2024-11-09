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
SECRET_ROLE_NAME = "秘密のロール"

joined_members_introductions = {}
member_message_ids = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot or before.channel == after.channel or any(role.name == SECRET_ROLE_NAME for role in member.roles):
        return

    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    if before.channel is None and after.channel is not None:
        introduction = None
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                introduction = message.content
                break

        intro_text = introduction if introduction else "自己紹介が見つかりませんでした。"
        joined_members_introductions[member] = intro_text

        embed = discord.Embed(title=f"{member.display_name}さんの自己紹介", description=intro_text, color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url)
        sent_message = await after.channel.send(embed=embed)
        
        member_message_ids[member] = sent_message.id

    elif before.channel is not None and after.channel is None:
        joined_members_introductions.pop(member, None)

        if member in member_message_ids:
            message_id = member_message_ids.pop(member)
            message = await before.channel.fetch_message(message_id)
            await message.delete()

bot.run(TOKEN)

