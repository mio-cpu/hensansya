import discord
from discord.ext import commands
import os
import traceback
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.messages = True  # メッセージイベントを有効化
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332
ANONYMOUS_CHANNEL_ID = 1308900602578735114  # 目安箱のチャンネルID
SECRET_ROLE_NAME = "秘密のロール"

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

@bot.event
async def on_message(message):
    if message.channel.id != ANONYMOUS_CHANNEL_ID or message.author.bot:
        return

    try:
        # メッセージの内容を確認
        print(f"Received message content: '{message.content}'")

        # メッセージを削除
        await message.delete()

        # 内容が完全に空の場合をチェック
        if not message.content or message.content.strip() == "":
            await message.channel.send("匿名メッセージが空のため、送信できません。", delete_after=10)
            return

        # Embedを作成
        embed = discord.Embed(
            title="匿名メッセージ",
            description=message.content,  # メッセージ内容を表示
            color=discord.Color.blurple()
        )
        embed.set_footer(text="目安箱より")

        # Embedを送信
        await message.channel.send(embed=embed)

    except Exception as e:
        print(f"Error in on_message: {e}")
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

bot.run(TOKEN)
