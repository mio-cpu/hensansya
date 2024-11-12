import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')

# 設定ファイルのパス
SETTINGS_FILE = "bot_settings.json"

# 初期設定
settings = {
    "INTRO_CHANNEL_ID": None,
    "SECRET_ROLE_NAMES": []
}

# 設定をJSONファイルから読み込む関数
def load_settings():
    global settings
    try:
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file)
    except FileNotFoundError:
        save_settings()  # ファイルがない場合、初期値で保存

# 設定をJSONファイルに保存する関数
def save_settings():
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)

# ボットが起動したときに設定を読み込む
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    load_settings()
    await bot.tree.sync()

@bot.tree.command(name="set_intro_channel", description="自己紹介チャンネルのIDを設定します")
async def set_intro_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    settings["INTRO_CHANNEL_ID"] = channel.id
    save_settings()
    await interaction.response.send_message(f"自己紹介チャンネルを {channel.mention} に設定しました。", ephemeral=True)

@bot.tree.command(name="add_secret_role", description="ボットが反応しないロールを追加します")
async def add_secret_role(interaction: discord.Interaction, role: discord.Role):
    if role.name not in settings["SECRET_ROLE_NAMES"]:
        settings["SECRET_ROLE_NAMES"].append(role.name)
        save_settings()
        await interaction.response.send_message(f"秘密のロール '{role.name}' を追加しました。", ephemeral=True)
    else:
        await interaction.response.send_message(f"'{role.name}' は既に追加されています。", ephemeral=True)

@bot.tree.command(name="remove_secret_role", description="ボットが反応しないロールを削除します")
async def remove_secret_role(interaction: discord.Interaction, role: discord.Role):
    if role.name in settings["SECRET_ROLE_NAMES"]:
        settings["SECRET_ROLE_NAMES"].remove(role.name)
        save_settings()
        await interaction.response.send_message(f"秘密のロール '{role.name}' を削除しました。", ephemeral=True)
    else:
        await interaction.response.send_message(f"'{role.name}' は秘密のロールに設定されていません。", ephemeral=True)

async def get_intro_message(member):
    intro_channel = bot.get_channel(settings["INTRO_CHANNEL_ID"])
    if not intro_channel:
        return None

    async for message in intro_channel.history(limit=500):
        if message.author == member:
            return message.content
    return "自己紹介が見つかりませんでした。"

active_members = []
last_embed_messages = {}

async def post_individual_embeds(channel):
    for message in last_embed_messages.values():
        await message.delete()
    last_embed_messages.clear()

    for member in active_members:
        intro_text = await get_intro_message(member)
        if intro_text:
            embed = discord.Embed(title=f"{member.display_name}の自己紹介", description=intro_text, color=discord.Color.blue())
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            last_embed_messages[member] = await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    if any(role.name in settings["SECRET_ROLE_NAMES"] for role in member.roles):
        return

    if after.channel and (before.channel is None or before.channel.id != after.channel.id):
        if member not in active_members:
            active_members.append(member)
        await post_individual_embeds(after.channel)

    elif before.channel and (after.channel is None or before.channel.id != after.channel.id):
        if member in active_members:
            active_members.remove(member)
            if member in last_embed_messages:
                await last_embed_messages[member].delete()
                del last_embed_messages[member]
        if before.channel:
            await post_individual_embeds(before.channel)

bot.run(TOKEN)
