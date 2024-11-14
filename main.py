import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332
SECRET_ROLE_NAME = "秘密のロール"

introductions = {}

@bot.event
async def on_ready():
    try:
        print(f'Logged in as {bot.user}')
    except Exception as e:
        print(f"Error in on_ready: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot or before.channel == after.channel:
            return

        if any(role.name == SECRET_ROLE_NAME for role in member.roles):
            return

        intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
        
        if after.channel and before.channel is None:
            async for message in intro_channel.history(limit=500):
                if message.author == member:
                    introductions[member.id] = message.content
                    break
            else:
                introductions[member.id] = "自己紹介が見つかりませんでした。"

            await update_introduction_messages(after.channel)

        elif before.channel and after.channel is None:
            if member.id in introductions:
                del introductions[member.id]

            await update_introduction_messages(before.channel)

    except Exception as e:
        print(f"Error in on_voice_state_update: {e}")

async def update_introduction_messages(channel):
    await channel.purge(limit=100, check=lambda m: m.author == bot.user)

    for user_id, intro_text in introductions.items():
        user = bot.get_user(user_id)
        embed = discord.Embed(title=f"{user.display_name}の自己紹介", color=discord.Color.blue())
        embed.add_field(name="自己紹介", value=intro_text, inline=False)
        embed.set_thumbnail(url=user.avatar.url)
        await channel.send(embed=embed)

bot.run(TOKEN)
