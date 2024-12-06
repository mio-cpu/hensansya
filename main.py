import discord
from discord.ext import commands
import os
import traceback
import json
from dotenv import load_dotenv

# 環境変数を読み込む
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("Error: DISCORD_TOKEN is not set. Please set it as an environment variable.")
    exit(1)

# Botの設定
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)
GUILD_ID = 1311062725207658546  # サーバーIDを適切に設定

# 設定管理クラス
class BotSettings:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.data = {"INTRO_CHANNEL_ID": None, "SECRET_ROLE_ID": None}
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.filename):
            self.save_settings()
        with open(self.filename, "r") as file:
            self.data = json.load(file)

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

# Botイベント
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    guild = discord.Object(id=GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands for guild {GUILD_ID}")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        traceback.print_exc()

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot or before.channel == after.channel:
            return

        # ロールIDで比較
        secret_role_id = settings.secret_role_id
        if secret_role_id and any(role.id == secret_role_id for role in member.roles):
            print(f"Skipping introduction for {member.display_name} due to secret role.")
            return

        intro_channel = bot.get_channel(settings.intro_channel_id)
        if not intro_channel:
            print("Error: Intro channel not set or not found.")
            return

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
    if channel.id not in introductions or not introductions[channel.id]:
        return

    for user_id, intro_text in introductions[channel.id].items():
        user = bot.get_user(user_id)
        if user and channel.guild.get_member(user.id).voice.channel == channel:
            embed = discord.Embed(title=f"{user.display_name}の自己紹介", color=discord.Color.blue())
            embed.add_field(name="自己紹介", value=intro_text, inline=False)
            embed.set_thumbnail(url=user.avatar.url)
            await channel.send(embed=embed)

# スラッシュコマンド
@bot.tree.command(name="設定", description="自己紹介チャンネルIDと秘密のロールIDを設定します")
async def set_config(interaction: discord.Interaction, intro_channel_id: str, secret_role_id: str):
    try:
        settings.intro_channel_id = int(intro_channel_id)
        settings.secret_role_id = int(secret_role_id)
        await interaction.response.send_message("設定が保存されました。", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("無効なIDが入力されました。", ephemeral=True)

bot.run(TOKEN)
