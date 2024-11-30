import discord
from discord.ext import commands
import os
import json
import traceback

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

# トークンを環境変数から取得
TOKEN = os.getenv('DISCORD_TOKEN')

# 設定を保持するための JSON ファイルのパス
CONFIG_FILE = "config.json"

# JSONファイルから設定を読み込む
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"INTRO_CHANNEL_ID": None, "SECRET_ROLE_NAME": None}

# 設定をJSONファイルに保存する
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

config = load_config()
INTRO_CHANNEL_ID = config.get("INTRO_CHANNEL_ID")
SECRET_ROLE_NAME = config.get("SECRET_ROLE_NAME")

introductions = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

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

# スラッシュコマンドで INTRO_CHANNEL_ID を設定する
@bot.tree.command(name="set_intro_channel", description="自己紹介チャンネルを設定します")
async def set_intro_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global INTRO_CHANNEL_ID
    INTRO_CHANNEL_ID = channel.id
    config["INTRO_CHANNEL_ID"] = INTRO_CHANNEL_ID
    save_config(config)
    await interaction.response.send_message(f"自己紹介チャンネルを {channel.mention} に設定しました。", ephemeral=True)

# スラッシュコマンドで SECRET_ROLE_NAME を設定する
@bot.tree.command(name="set_secret_role", description="秘密のロールを設定します")
async def set_secret_role(interaction: discord.Interaction, role: discord.Role):
    global SECRET_ROLE_NAME
    SECRET_ROLE_NAME = role.name
    config["SECRET_ROLE_NAME"] = SECRET_ROLE_NAME
    save_config(config)
    await interaction.response.send_message(f"秘密のロールを `{SECRET_ROLE_NAME}` に設定しました。", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == INTRO_CHANNEL_ID:
        introductions[message.author.id] = message.content
        await update_introduction_messages_in_voice_channels(message.author)

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if after.channel.id == INTRO_CHANNEL_ID and not after.author.bot:
        introductions[after.author.id] = after.content
        await update_introduction_messages_in_voice_channels(after.author)

async def update_introduction_messages_in_voice_channels(member):
    for voice_channel in member.guild.voice_channels:
        if member.id in introductions.get(voice_channel.id, {}):
            await update_introduction_messages(voice_channel)

bot.run(TOKEN)
