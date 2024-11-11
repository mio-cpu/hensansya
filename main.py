import discord
from discord.ext import commands
import os
import sqlite3

# データベースファイルのパスを設定
DB_FILE = '/bot/data/bot_config.db'  # Dockerのボリュームに保存

# Botの初期設定
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# トークンを環境変数から取得
TOKEN = os.getenv('DISCORD_TOKEN')

# 初期化用のグローバル変数
active_members = []
last_embed_messages = {}

# データベースの初期化
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

# データベースから設定を取得
def get_config(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT value FROM config WHERE key = ?', (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# データベースに設定を保存
def set_config(key, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('REPLACE INTO config (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

# 設定ファイルから読み込み
INTRO_CHANNEL_ID = int(get_config('intro_channel_id')) if get_config('intro_channel_id') else None
SECRET_ROLE_NAME = get_config('secret_role_name')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # スラッシュコマンドを同期
    await bot.tree.sync()

@bot.tree.command(name="set_intro_channel", description="自己紹介チャンネルのIDを設定します")
async def set_intro_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global INTRO_CHANNEL_ID
    INTRO_CHANNEL_ID = channel.id
    set_config('intro_channel_id', str(channel.id))
    await interaction.response.send_message(f"自己紹介チャンネルを {channel.mention} に設定しました。", ephemeral=True)

@bot.tree.command(name="set_secret_role", description="ボットが反応しないロール名を設定します")
async def set_secret_role(interaction: discord.Interaction, role: discord.Role):
    global SECRET_ROLE_NAME
    SECRET_ROLE_NAME = role.name
    set_config('secret_role_name', role.name)
    await interaction.response.send_message(f"秘密のロールを '{role.name}' に設定しました。", ephemeral=True)

async def get_intro_message(member):
    # 自己紹介チャンネルが設定されていない場合はNoneを返す
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
    if not intro_channel:
        return None

    # 自己紹介メッセージを検索
    async for message in intro_channel.history(limit=500):
        if message.author == member:
            return message.content
    return "自己紹介が見つかりませんでした。"

async def post_individual_embeds(channel):
    # 前回のメッセージをすべて削除
    for message in last_embed_messages.values():
        await message.delete()
    last_embed_messages.clear()

    # メンバーごとにEmbedを投稿
    for member in active_members:
        intro_text = await get_intro_message(member)
        if intro_text:
            embed = discord.Embed(title=f"{member.display_name}の自己紹介", description=intro_text, color=discord.Color.blue())
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            last_embed_messages[member] = await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    # ボットが反応しないロールが設定されている場合、そのロールを持つメンバーを除外
    if SECRET_ROLE_NAME:
        secret_role = discord.utils.get(member.guild.roles, name=SECRET_ROLE_NAME)
        if secret_role in member.roles:
            return

    # 通話チャンネルに入室した場合の処理
    if after.channel and (before.channel is None or before.channel.id != after.channel.id):
        if member not in active_members:
            active_members.append(member)
        await post_individual_embeds(after.channel)

    # 通話チャンネルから退出した場合の処理
    elif before.channel and (after.channel is None or before.channel.id != after.channel.id):
        if member in active_members:
            active_members.remove(member)
            # 退出したメンバーの自己紹介を削除
            if member in last_embed_messages:
                await last_embed_messages[member].delete()
                del last_embed_messages[member]
        # 他のアクティブなメンバーの自己紹介を再投稿
        if before.channel:
            await post_individual_embeds(before.channel)

# データベースの初期化を実行
init_db()

# Botを起動
bot.run(TOKEN)

