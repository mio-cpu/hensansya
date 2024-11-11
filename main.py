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

active_members = []
last_embed_message = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

async def get_intro_message(member):
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
    async for message in intro_channel.history(limit=500):
        if message.author == member:
            return message.content
    return "自己紹介が見つかりませんでした。"

async def update_voice_channel_embed(channel):
    global last_embed_message
    embed = discord.Embed(title="ボイスチャンネルの自己紹介", color=discord.Color.blue())
    for member in active_members:
        intro_text = await get_intro_message(member)
        embed.add_field(name=member.display_name, value=intro_text, inline=False)
    
    if last_embed_message:
        await last_embed_message.delete()

    last_embed_message = await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    secret_role = discord.utils.get(member.guild.roles, name=SECRET_ROLE_NAME)

    if secret_role in member.roles:
        return

    if after.channel and (before.channel is None or before.channel.id != after.channel.id):
        if member not in active_members:
            active_members.append(member)
        await update_voice_channel_embed(after.channel)
    elif before.channel and (after.channel is None or before.channel.id != after.channel.id):
        if member in active_members:
            active_members.remove(member)
        if before.channel:
            await update_voice_channel_embed(before.channel)

bot.run(TOKEN)
