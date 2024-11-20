import discord
from discord.ext import commands
import os

# 必要な権限を有効にした Intents を定義
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.voice_states = True

# Bot の定義
bot = commands.Bot(command_prefix="!", intents=intents)

# 環境変数からトークンを取得
TOKEN = os.getenv('DISCORD_TOKEN')

# 設定
INTRO_CHANNEL_ID = 1285729396971274332  # 自己紹介チャンネルID
ANONYMOUS_CHANNEL_ID = 1308544883899764746  # 匿名メッセージ用チャンネルID
SECRET_ROLE_NAME = "秘密のロール"  # BOTが反応しないロール名


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)

    # チャンネルに移動した場合、自己紹介を送信
    if after.channel and (before.channel != after.channel):
        if any(role.name == SECRET_ROLE_NAME for role in member.roles):
            return  # 指定のロールを持つユーザーはスキップ

        messages = []
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                messages.append(message)

        channel = after.channel

        # 過去の BOT メッセージを削除
        await channel.purge(limit=100, check=lambda m: m.author == bot.user)

        if messages:
            for msg in messages:
                embed = discord.Embed(
                    title=f"{member.display_name}さんの自己紹介",
                    description=msg.content,
                    color=discord.Color.blue(),
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else "")
                await channel.send(embed=embed)
        else:
            await channel.send(
                f"{member.display_name}さんが入室しましたが、自己紹介が見つかりませんでした。"
            )


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # 匿名メッセージ用チャンネルでの処理
    if message.channel.id == ANONYMOUS_CHANNEL_ID:
        try:
            # 元のメッセージ内容を取得
            original_content = message.content.strip()
            
            # 空メッセージを確認
            if not original_content:
                await message.delete()
                await message.channel.send("匿名のメッセージは空白にはできません。")
                return

            # メッセージを削除
            await message.delete()

            # 匿名メッセージとして再送信
            await message.channel.send(f"匿名のメッセージ: {original_content}")
        except discord.Forbidden:
            print("メッセージの削除権限がありません。")
        except discord.HTTPException as e:
            print(f"エラーが発生しました: {e}")

    # 他のコマンドを処理
    await bot.process_commands(message)


# Bot を実行
bot.run(TOKEN)
