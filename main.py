import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ボットの初期化
bot.voice_channel_map = {}  # {channel_id: {user_id: intro_text}}

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    # ユーザーがボイスチャンネルを移動した場合
    if before.channel != after.channel:
        await handle_introduction_update(member, before.channel, after.channel)

async def handle_introduction_update(member, before_channel, after_channel):
    if before_channel:
        # 退室時の処理
        if before_channel.id in bot.voice_channel_map:
            if member.id in bot.voice_channel_map[before_channel.id]:
                del bot.voice_channel_map[before_channel.id][member.id]
            # チャンネルが空なら辞書から削除
            if not bot.voice_channel_map[before_channel.id]:
                del bot.voice_channel_map[before_channel.id]
        await update_introduction_messages(before_channel)

    if after_channel:
        # 入室時の処理
        if after_channel.id not in bot.voice_channel_map:
            bot.voice_channel_map[after_channel.id] = {}
        # ユーザーの自己紹介を仮登録（後で更新可能）
        bot.voice_channel_map[after_channel.id][member.id] = f"{member.display_name}の仮の自己紹介"
        await update_introduction_messages(after_channel)

async def update_introduction_messages(channel):
    # メッセージ削除処理
    try:
        await channel.purge(
            limit=100,
            check=lambda m: (
                m.author == bot.user and
                m.embeds and
                "自己紹介" in m.embeds[0].title
            )
        )
    except discord.errors.NotFound:
        print(f"Message not found during purge in {channel.name}")
    except Exception as e:
        print(f"Unexpected error during purge: {e}")

    # チャンネルの自己紹介マップが存在しない場合は終了
    if channel.id not in bot.voice_channel_map:
        return

    # 辞書のコピーを作成してループ
    voice_channel_map_copy = bot.voice_channel_map[channel.id].copy()
    for user_id, intro_text in voice_channel_map_copy.items():
        user = bot.get_user(user_id)
        member = channel.guild.get_member(user_id)

        # ユーザーが現在そのチャンネルにいる場合のみ処理
        if member and member.voice and member.voice.channel == channel:
            try:
                # Embed を作成して送信
                embed = discord.Embed(
                    title=f"{user.display_name}の自己紹介",
                    description=intro_text if intro_text.strip() else "（内容が登録されていません）",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending introduction message for {user.display_name}: {e}")

# コマンド：自己紹介を更新
@bot.command()
async def set_intro(ctx, *, intro_text):
    # ユーザーが現在のボイスチャンネルにいるか確認
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel

        # ユーザーの自己紹介を更新
        if channel.id not in bot.voice_channel_map:
            bot.voice_channel_map[channel.id] = {}
        bot.voice_channel_map[channel.id][ctx.author.id] = intro_text

        await ctx.send(f"{ctx.author.display_name}さんの自己紹介を更新しました！")
        # 自己紹介メッセージを再生成
        await update_introduction_messages(channel)
    else:
        await ctx.send("ボイスチャンネルに参加していません！")

# トークンを環境変数から取得して実行
import os
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(TOKEN)
