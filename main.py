import discord
from discord.ext import commands
import os

# Botの初期設定
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 環境変数からトークンを取得
TOKEN = os.getenv('DISCORD_TOKEN')

# 自己紹介チャンネルのIDを設定
INTRO_CHANNEL_ID = 1285729396971274332  # 自己紹介チャンネルのID

# 通話チャンネルに参加しているメンバーの自己紹介を管理する辞書
joined_members_introductions = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    # 入退室がない場合は何もしない
    if before.channel == after.channel:
        return

    # 自己紹介チャンネルを取得
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    # メンバーが通話チャンネルに新しく参加した場合
    if before.channel is None and after.channel is not None:
        introduction = None

        # 自己紹介チャンネルのメッセージを検索して自己紹介を取得
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                introduction = message.content
                break

        # 自己紹介が見つかった場合は辞書に追加、見つからない場合は通知メッセージ
        if introduction:
            joined_members_introductions[member] = introduction
        else:
            joined_members_introductions[member] = "自己紹介が見つかりませんでした。"

    # メンバーが通話チャンネルから退出した場合、辞書から削除
    elif before.channel is not None and after.channel is None:
        if member in joined_members_introductions:
            del joined_members_introductions[member]

    # 参加している全メンバーの自己紹介を再投稿
    if after.channel is not None or (before.channel is not None and after.channel is None):
        # Embedメッセージを準備
        embed = discord.Embed(title="現在の参加メンバーの自己紹介", color=discord.Color.blue())
        for m, intro in joined_members_introductions.items():
            # メンバーごとにアバター付きで自己紹介を追加
            embed.add_field(name=m.display_name, value=intro, inline=False)
            embed.set_thumbnail(url=m.avatar.url)

        # 通話チャンネルが存在する場合にのみ送信
        if after.channel:
            await after.channel.send(embed=embed)

# Botを実行
bot.run(TOKEN)
