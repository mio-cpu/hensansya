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
bot.introductions = {}  # {member_id: intro_text}
bot.voice_channel_map = {}  # {channel_id: {member_id: intro_text}}

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
        if member.bot:
            return

        # 秘密のロールを持つメンバーを無視
        secret_role = discord.utils.get(member.guild.roles, name=SECRET_ROLE_NAME)
        if secret_role in member.roles:
            return

        # チャンネル変更を検出（マイクやカメラのオン/オフは無視）
        if before.channel != after.channel:
            if not before.channel and after.channel:
                # 新しいチャンネルに参加
                await handle_introduction_update(member, None, after.channel)
            elif before.channel and not after.channel:
                # チャンネルから退出
                await handle_introduction_update(member, before.channel, None)
            elif before.channel and after.channel:
                # チャンネルを移動
                await handle_introduction_update(member, before.channel, after.channel)

    except Exception as e:
        print(f"Error in on_voice_state_update: {e}")
        traceback.print_exc()

# 自己紹介更新処理
async def handle_introduction_update(member, before_channel, after_channel):
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    # 退出処理
    if before_channel:
        bot.voice_channel_map.get(before_channel.id, {}).pop(member.id, None)
        await update_introduction_messages(before_channel)

    # 参加処理
    if after_channel:
        intro_text = await get_or_fetch_introduction(member, intro_channel)
        if after_channel.id not in bot.voice_channel_map:
            bot.voice_channel_map[after_channel.id] = {}
        bot.voice_channel_map[after_channel.id][member.id] = intro_text
        await update_introduction_messages(after_channel)

# 自己紹介を取得またはキャッシュから取得
async def get_or_fetch_introduction(member, intro_channel):
    # キャッシュから取得
    if member.id in bot.introductions:
        intro_text = bot.introductions[member.id]
        if intro_text:  # 内容が空でないことを確認
            return intro_text

    # チャンネル履歴から取得
    async for message in intro_channel.history(limit=500):
        if message.author == member and message.content.strip():  # 空白でない内容
            bot.introductions[member.id] = message.content
            return message.content

    # 自己紹介が見つからない場合
    return "自己紹介が登録されていません。自己紹介チャンネルで自己紹介を投稿してください。"

# 自己紹介のメッセージを更新
async def update_introduction_messages(channel):
    # 既存の自己紹介メッセージを削除
    await channel.purge(limit=100, check=lambda m: m.author == bot.user and m.embeds and "自己紹介" in m.embeds[0].title)

    if channel.id not in bot.voice_channel_map:
        return

    # 新しい自己紹介メッセージを送信
    for user_id, intro_text in bot.voice_channel_map[channel.id].items():
        user = bot.get_user(user_id)
        member = channel.guild.get_member(user_id)

        if member and member.voice and member.voice.channel == channel:
            # Embed の生成
            embed = discord.Embed(
                title=f"{user.display_name}の自己紹介",
                description=intro_text if intro_text.strip() else "（内容が登録されていません）",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            await channel.send(embed=embed)

# メッセージ送信時のイベント
@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        if message.channel.id == INTRO_CHANNEL_ID:
            bot.introductions[message.author.id] = message.content
            await update_introduction_messages_in_voice_channels(message.author)

        await bot.process_commands(message)
    except Exception as e:
        print(f"Error in on_message: {e}")
        traceback.print_exc()

# メッセージ編集時のイベント
@bot.event
async def on_message_edit(before, after):
    try:
        if after.channel.id == INTRO_CHANNEL_ID and not after.author.bot:
            bot.introductions[after.author.id] = after.content
            await update_introduction_messages_in_voice_channels(after.author)
    except Exception as e:
        print(f"Error in on_message_edit: {e}")
        traceback.print_exc()

# 全てのボイスチャンネルにおける自己紹介メッセージを更新
async def update_introduction_messages_in_voice_channels(member):
    for voice_channel in member.guild.voice_channels:
        if member.id in bot.voice_channel_map.get(voice_channel.id, {}):
            await update_introduction_messages(voice_channel)

# Bot の起動
bot.run(TOKEN)
