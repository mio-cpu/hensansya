import discord
from discord.ext import commands
import os
import traceback

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332  # 自己紹介チャンネルのID
ANONYMOUS_CHANNEL_ID = 1308544883899764746  # 目安箱チャンネルのID
SECRET_ROLE_NAME = "秘密のロール"

# ブロックする不適切な言葉リスト
BLOCKED_WORDS = ["暴言1", "卑猥な言葉2", "禁止語句3"]  # 具体的な単語を追加

introductions = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot or before.channel == after.channel:
            return

        if any(role.name == SECRET_ROLE_NAME for role in member.roles):
            return

        intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

        if after.channel and before.channel is None:
            intro_text = await fetch_introduction(member, intro_channel)
            if after.channel.id not in introductions:
                introductions[after.channel.id] = {}
            introductions[after.channel.id][member.id] = intro_text
            await update_introduction_messages(after.channel)

        elif before.channel and after.channel is None:
            if before.channel.id in introductions and member.id in introductions[before.channel.id]:
                del introductions[before.channel.id][member.id]
            await update_introduction_messages(before.channel)

        elif before.channel and after.channel:
            if before.channel.id in introductions and member.id in introductions[before.channel.id]:
                del introductions[before.channel.id][member.id]
            intro_text = await fetch_introduction(member, intro_channel)
            if after.channel.id not in introductions:
                introductions[after.channel.id] = {}
            introductions[after.channel.id][member.id] = intro_text
            await update_introduction_messages(before.channel)
            await update_introduction_messages(after.channel)

    except Exception as e:
        print(f"Error in on_voice_state_update: {e}")
        traceback.print_exc()

async def fetch_introduction(member, intro_channel):
    async for message in intro_channel.history(limit=500):
        if message.author == member:
            return message.content
    return "自己紹介が見つかりませんでした。"

async def update_introduction_messages(channel):
    await channel.purge(limit=100, check=lambda m: m.author == bot.user)
    if channel.id not in introductions:
        return

    for user_id, intro_text in introductions[channel.id].items():
        user = bot.get_user(user_id)
        if user and channel.guild.get_member(user.id).voice.channel == channel:
            embed = discord.Embed(title=f"{user.display_name}の自己紹介", color=discord.Color.blue())
            embed.add_field(name="自己紹介", value=intro_text, inline=False)
            embed.set_thumbnail(url=user.avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    if message.channel.id == ANONYMOUS_CHANNEL_ID:
        if any(blocked_word in message.content.lower() for blocked_word in BLOCKED_WORDS):
            await message.delete()
            await message.channel.send(f"{message.author.mention} 不適切な内容が含まれているため、投稿は許可されません。")
            return

        await message.delete()
        anonymous_message = message.content
        
        embed = discord.Embed(
            description=anonymous_message,
            color=discord.Color.gray()
        )
        embed.set_author(name="匿名のメッセージ")
        
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

bot.run(TOKEN)
