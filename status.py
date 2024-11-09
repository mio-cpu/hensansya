# status.py
import os
import discord
from discord.ext import commands

# 環境変数からBOTのトークンを取得
TOKEN = os.getenv("BOT_TOKEN")

# Botのインスタンスを作成
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Botが起動したときに実行されるイベント
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # カスタムステータスを「編纂中」に設定
    activity = discord.Activity(type=discord.ActivityType.custom, name="編纂中")
    await bot.change_presence(activity=activity)

# Botを起動
bot.run(TOKEN)
