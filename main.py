import discord
from discord.ext import commands
import os
import traceback

# Bot インスタンス設定
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.messages = True  # メッセージイベントに対応
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

# 環境変数からトークン取得
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise RuntimeError("環境変数 'DISCORD_TOKEN' が設定されていません。")

# 設定
INTRO_CHANNEL_ID = 1311065842624102400
SECRET_ROLE_NAME = "秘密のロール"

# ボット起動時に使用するデータ
bot.introductions = {}

# Bot 起動時のイベント
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# ボイスステート変更時のイベント
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        # ボットや同じチャンネル間の移動は無視
        if member.bot or before.channel == after.channel:
            return

        # 秘密のロールを持つメンバーを無視
        if any(role.name == SECRET_ROLE_NAME for role in member.roles):
            return

        # チャンネル情報の更新
        await handle_introduction_update(member, before.channel, after.channel)

    except Exception as e:
        print(f"Error in on_voice_state_update: {e}")
        traceback.print_exc()

# 自己紹介更新処理
async def handle_introduction_update(member, before_channel, after_channel):
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    if before_channel:
        bot.introductions.get(before_channel.id, {}).pop(member.id, None)
        await update_introduction_messages(before_channel)

    if after_channel:
        intro_text = await get_or_fetch_introduction(member, intro_channel)
        if after_channel.id not in bot.introductions:
            bot.introductions[after_channel.id] = {}
        bot.introductions[after_channel.id][member.id] = intro_text
        await update_introduction_messages(after_channel)

# 自己紹介を取得またはキャッシュから取得
async def get_or_fetch_introduction(member, intro_channel):
    if member.id in bot.introductions:
        return bot.introductions[member.id]

    async for message in intro_channel.history(limit=500):
        if message.author == member:
            bot.introductions[member.id] = message.content
            return message.content

    return "自己紹介が見つかりませんでした。"

# 自己紹介のメッセージを更新
async def update_introduction_messages(channel):
    await channel.purge(limit=100, check=lambda m: m.author == bot.user and m.embeds)

    if channel.id not in bot.introductions:
        return

    for user_id, intro_text in bot.introductions[channel.id].items():
        user = bot.get_user(user_id)
        if user and channel.guild.get_member(user.id).voice.channel == channel:
            embed = discord.Embed(title=f"{user.display_name}の自己紹介", color=discord.Color.blue())
            embed.add_field(name="自己紹介", value=intro_text, inline=False)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            await channel.send(embed=embed)

# メッセージ送信時のイベント
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == INTRO_CHANNEL_ID:
        bot.introductions[message.author.id] = message.content
        await update_introduction_messages_in_voice_channels(message.author)

    await bot.process_commands(message)

# メッセージ編集時のイベント
@bot.event
async def on_message_edit(before, after):
    if after.channel.id == INTRO_CHANNEL_ID and not after.author.bot:
        bot.introductions[after.author.id] = after.content
        await update_introduction_messages_in_voice_channels(after.author)

# 全てのボイスチャンネルにおける自己紹介メッセージを更新
async def update_introduction_messages_in_voice_channels(member):
    for voice_channel in member.guild.voice_channels:
        if member.id in bot.introductions.get(voice_channel.id, {}):
            await update_introduction_messages(voice_channel)

# Bot の起動
bot.run(TOKEN)
