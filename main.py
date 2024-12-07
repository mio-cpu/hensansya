import discord
from discord.ext import commands
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Botの初期化
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.messages = True
intents.message_content = True  # メッセージコンテンツ取得用
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

# 環境変数
TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = int(os.getenv('INTRO_CHANNEL_ID', 0))  # デフォルト値0
SECRET_ROLE_ID = int(os.getenv('SECRET_ROLE_ID', 0))      # デフォルト値0

# データ
introductions = {}

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.error(f"Error syncing commands: {e}", exc_info=True)

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot or before.channel == after.channel:
            return

        # SECRET_ROLE_ID を持つ役職があるか確認
        if any(role.id == SECRET_ROLE_ID for role in member.roles):
            return

        intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
        if not intro_channel:
            logger.error(f"INTRO_CHANNEL_ID {INTRO_CHANNEL_ID} is invalid or inaccessible.")
            return

        # 入退出イベント処理
        if after.channel and not before.channel:
            # 入室時
            intro_text = await fetch_introduction(member, intro_channel)
            introductions.setdefault(after.channel.id, {})[member.id] = intro_text
            await update_introduction_messages(after.channel)

        elif before.channel and not after.channel:
            # 退出時
            if before.channel.id in introductions and member.id in introductions[before.channel.id]:
                del introductions[before.channel.id][member.id]
            await update_introduction_messages(before.channel)

        elif before.channel and after.channel:
            # チャンネル移動時
            if before.channel.id in introductions and member.id in introductions[before.channel.id]:
                del introductions[before.channel.id][member.id]
            intro_text = await fetch_introduction(member, intro_channel)
            introductions.setdefault(after.channel.id, {})[member.id] = intro_text
            await update_introduction_messages(before.channel)
            await update_introduction_messages(after.channel)

    except Exception as e:
        logger.error(f"Error in on_voice_state_update: {e}", exc_info=True)

async def fetch_introduction(member, intro_channel):
    """効率的に自己紹介を取得"""
    try:
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                logger.info(f"Introduction found for {member.display_name}: {message.content}")
                return message.content

        logger.info(f"No introduction found for {member.display_name}")
        return "自己紹介が見つかりませんでした。"

    except Exception as e:
        logger.error(f"Error fetching introduction: {e}", exc_info=True)
        return "エラーが発生しました。"

async def update_introduction_messages(channel):
    """ボイスチャンネルの自己紹介メッセージを更新"""
    try:
        await channel.purge(limit=100, check=lambda m: m.author == bot.user)
        if channel.id not in introductions:
            return

        for user_id, intro_text in introductions[channel.id].items():
            user = bot.get_user(user_id)
            if user:
                embed = discord.Embed(title=f"{user.display_name}の自己紹介", color=discord.Color.blue())
                embed.add_field(name="自己紹介", value=intro_text, inline=False)
                embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
                await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Error updating messages in {channel.name}: {e}", exc_info=True)

bot.run(TOKEN)
