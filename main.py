import discord
from discord.ext import commands
import os
import traceback
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 環境変数を読み込む
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))  # 環境変数で管理

if not TOKEN:
    print("Error: DISCORD_TOKEN is not set. Please check your .env file.")
    exit(1)

if not GUILD_ID:
    print("Error: DISCORD_GUILD_ID is not set. Please check your .env file.")
    exit(1)

# Botの設定
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

# 設定管理クラス
class BotSettings:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.data = {"INTRO_CHANNEL_ID": None, "SECRET_ROLE_ID": None}
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.filename):
            self.save_settings()
        try:
            with open(self.filename, "r") as file:
                self.data = json.load(file)
        except (json.JSONDecodeError, IOError):
            print("Error: Invalid settings.json. Reinitializing...")
            self.data = {"INTRO_CHANNEL_ID": None, "SECRET_ROLE_ID": None}
            self.save_settings()

    def save_settings(self):
        with open(self.filename, "w") as file:
            json.dump(self.data, file)

    @property
    def intro_channel_id(self):
        return self.data.get("INTRO_CHANNEL_ID")

    @intro_channel_id.setter
    def intro_channel_id(self, value):
        self.data["INTRO_CHANNEL_ID"] = value
        self.save_settings()

    @property
    def secret_role_id(self):
        return self.data.get("SECRET_ROLE_ID")

    @secret_role_id.setter
    def secret_role_id(self, value):
        self.data["SECRET_ROLE_ID"] = value
        self.save_settings()

settings = BotSettings()
introductions = {}
introduction_cache = {}

# エラーをログファイルに記録
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f"error_{datetime.now().strftime('%Y-%m-%d')}.log")

def log_error(message):
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{datetime.now()}: {message}\n")

# Botイベント
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    guild = discord.Object(id=GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands for guild {GUILD_ID}")
    except Exception as e:
        error_message = f"Error syncing commands: {e}"
        log_error(error_message)
        traceback.print_exc()

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot or before.channel == after.channel:
            return

        secret_role_id = settings.secret_role_id
        if secret_role_id and any(role.id == secret_role_id for role in member.roles):
            print(f"Skipping introduction for {member.display_name} due to secret role.")
            return

        intro_channel = bot.get_channel(settings.intro_channel_id)
        if not intro_channel:
            print("Error: Intro channel not set or not found.")
            return

        current_time = datetime.now()

        # チャンネル参加
        if after.channel and before.channel is None:
            intro_text = await fetch_introduction(member, intro_channel)
            introductions.setdefault(after.channel.id, {})[member.id] = {
                "intro": intro_text,
                "timestamp": current_time,
            }
            await update_introduction_messages(after.channel)

        # チャンネル退出
        elif before.channel and after.channel is None:
            if before.channel.id in introductions:
                introductions[before.channel.id].pop(member.id, None)
            await update_introduction_messages(before.channel)

        # チャンネル移動
        elif before.channel and after.channel:
            if before.channel.id in introductions:
                introductions[before.channel.id].pop(member.id, None)
            intro_text = await fetch_introduction(member, intro_channel)
            introductions.setdefault(after.channel.id, {})[member.id] = {
                "intro": intro_text,
                "timestamp": current_time,
            }
            await update_introduction_messages(before.channel)
            await update_introduction_messages(after.channel)

        # 古いデータを削除
        for channel_id in list(introductions.keys()):
            introductions[channel_id] = {
                user_id: data
                for user_id, data in introductions[channel_id].items()
                if current_time - data["timestamp"] <= timedelta(hours=1)
            }
            if not introductions[channel_id]:
                del introductions[channel_id]

    except Exception as e:
        error_message = f"Error in on_voice_state_update: {e}"
        log_error(error_message)
        traceback.print_exc()

async def fetch_introduction(member, intro_channel):
    if member.id in introduction_cache:
        return introduction_cache[member.id]

    async for message in intro_channel.history(limit=500):
        if message.author == member:
            introduction_cache[member.id] = message.content
            return message.content

    return "自己紹介が見つかりませんでした。"

async def update_introduction_messages(channel):
    def is_bot_message(m):
        return m.author == bot.user

    await channel.purge(limit=100, check=is_bot_message)
    if channel.id not in introductions or not introductions[channel.id]:
        return

    for user_id, data in introductions[channel.id].items():
        user = bot.get_user(user_id)
        if user:
            member = channel.guild.get_member(user.id)
            if member and member.voice and member.voice.channel == channel:
                avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
                embed = discord.Embed(title=f"{user.display_name}の自己紹介", color=discord.Color.blue())
                embed.add_field(name="自己紹介", value=data["intro"], inline=False)
                embed.set_thumbnail(url=avatar_url)
                await channel.send(embed=embed)

# スラッシュコマンド
@bot.tree.command(name="設定", description="自己紹介チャンネルIDと秘密のロールIDを設定します")
async def set_config(interaction: discord.Interaction, intro_channel_id: str, secret_role_id: str):
    try:
        intro_channel = bot.get_channel(int(intro_channel_id))
        secret_role = interaction.guild.get_role(int(secret_role_id))
        if not intro_channel:
            await interaction.response.send_message("指定されたチャンネルIDが無効です。", ephemeral=True)
            return
        if not secret_role:
            await interaction.response.send_message("指定されたロールIDが無効です。", ephemeral=True)
            return

        settings.intro_channel_id = int(intro_channel_id)
        settings.secret_role_id = int(secret_role_id)
        await interaction.response.send_message("設定が保存されました。", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("無効なIDが入力されました。", ephemeral=True)

bot.run(TOKEN)
