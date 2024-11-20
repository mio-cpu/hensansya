import discord
from discord.ext import commands
import os
import traceback

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332
SECRET_ROLE_NAME = "秘密のロール"

introductions = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        # スラッシュコマンドを同期
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

# 匿名メッセージを送信するスラッシュコマンドの追加
@bot.tree.command(name="匿名メッセージ", description="BOTが代わりに匿名でメッセージを送信します")
async def anonymous_message(interaction: discord.Interaction, message: str):
    """スラッシュコマンドによる匿名メッセージ送信"""
    try:
        await interaction.response.defer(ephemeral=True)  # ユーザーには一時的な応答を表示
        # メッセージをチャンネルに投稿
        await interaction.channel.send(message)
        # ユーザーに成功の通知
        await interaction.followup.send("メッセージを匿名で送信しました！", ephemeral=True)
    except Exception as e:
        # エラーが発生した場合
        await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=True)
        print(f"Error in anonymous_message: {e}")
        traceback.print_exc()

bot.run(TOKEN)
