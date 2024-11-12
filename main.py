import discord
from discord.ext import commands
import os
import sqlite3

DB_FILE = '/bot/data/bot_config.db'  # データベースファイルのパス
intents = discord.Intents.all()  # 全てのインテントを許可
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')
active_members = []
last_embed_messages = {}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

def get_config(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT value FROM config WHERE key = ?', (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_config(key, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

INTRO_CHANNEL_ID = int(get_config('intro_channel_id')) if get_config('intro_channel_id') else None
SECRET_ROLE_NAMES = get_config('secret_role_names').split(',') if get_config('secret_role_names') else []

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync(guild=discord.Object(id=1285691131446825105))  # 特定のサーバーで同期
    print("Slash commands synchronized!")

@bot.tree.command(name="set_intro_channel", description="自己紹介チャンネルのIDを設定します")
async def set_intro_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global INTRO_CHANNEL_ID
    INTRO_CHANNEL_ID = channel.id
    set_config('intro_channel_id', str(channel.id))
    await interaction.response.send_message(f"自己紹介チャンネルを {channel.mention} に設定しました。", ephemeral=True)

@bot.tree.command(name="set_secret_roles", description="ボットが反応しないロール名を設定します")
async def set_secret_roles(interaction: discord.Interaction, *roles: discord.Role):
    global SECRET_ROLE_NAMES
    SECRET_ROLE_NAMES = [role.name for role in roles]
    set_config('secret_role_names', ','.join(SECRET_ROLE_NAMES))
    await interaction.response.send_message(f"秘密のロールを '{', '.join(SECRET_ROLE_NAMES)}' に設定しました。", ephemeral=True)

async def get_intro_message(member):
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
    if not intro_channel:
        return None
    async for message in intro_channel.history(limit=500):
        if message.author == member:
            return message.content
    return "自己紹介が見つかりませんでした。"

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
    if any(role.name in SECRET_ROLE_NAMES for role in member.roles):
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

init_db()
bot.run(TOKEN)
