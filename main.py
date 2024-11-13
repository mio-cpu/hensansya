import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332  # 自己紹介チャンネルのID
SECRET_ROLE_NAME = "秘密のロール"  # 反応しない役職名

# 自己紹介メッセージの保存用辞書
introductions = {}

@bot.event
async def on_ready():
    try:
        print(f'Logged in as {bot.user}')
    except Exception as e:
        print(f"Error in on_ready: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        if member.bot or before.channel == after.channel:
            return

        # 秘密のロールを持っている場合、処理をスキップ
        if any(role.name == SECRET_ROLE_NAME for role in member.roles):
            return

        intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
        if after.channel and before.channel is None:
            async for message in intro_channel.history(limit=500):
                if message.author == member:
                    introductions[member.id] = message.content
                    break
            else:
                introductions[member.id] = "自己紹介が見つかりませんでした。"

            # 既存のEmbedを削除し、新しいEmbedを生成して送信
            await after.channel.purge(limit=100, check=lambda m: m.author == bot.user)
            embed = discord.Embed(title="現在の参加者と自己紹介", color=discord.Color.blue())
            for user_id, intro_text in introductions.items():
                user = bot.get_user(user_id)
                embed.add_field(name=user.display_name, value=intro_text, inline=False)
            await after.channel.send(embed=embed)

        elif before.channel and after.channel is None:
            if member.id in introductions:
                del introductions[member.id]
            await before.channel.purge(limit=100, check=lambda m: m.author == bot.user)
            embed = discord.Embed(title="現在の参加者と自己紹介", color=discord.Color.blue())
            for user_id, intro_text in introductions.items():
                user = bot.get_user(user_id)
                embed.add_field(name=user.display_name, value=intro_text, inline=False)
            if introductions:
                await before.channel.send(embed=embed)
    except Exception as e:
        print(f"Error in on_voice_state_update: {e}")

bot.run(TOKEN)
