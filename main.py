import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')
INTRO_CHANNEL_ID = 1285729396971274332
SECRET_ROLE_NAME = "秘密のロール"

active_members = []
last_embed_messages = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

async def get_intro_message(member):
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
    async for message in intro_channel.history(limit=500):
        if message.author == member:
            return message.content
    return "自己紹介が見つかりませんでした。"

async def post_individual_embeds(channel):
    # 既存のEmbedメッセージをすべて削除
    for message in last_embed_messages.values():
        await message.delete()
    last_embed_messages.clear()

    # 現在の参加メンバー全員分のEmbedを新規に作成して投稿
    for member in active_members:
        intro_text = await get_intro_message(member)
        embed = discord.Embed(title=f"{member.display_name}の自己紹介", description=intro_text, color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

        # Embedをチャンネルに送信し、辞書に保存
        last_embed_messages[member] = await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    secret_role = discord.utils.get(member.guild.roles, name=SECRET_ROLE_NAME)

    # 秘密のロールを持っているメンバーを無視
    if secret_role in member.roles:
        return

    # メンバーがボイスチャンネルに入室した場合
    if after.channel and (before.channel is None or before.channel.id != after.channel.id):
        if member not in active_members:
            active_members.append(member)
        await post_individual_embeds(after.channel)

    # メンバーがボイスチャンネルから退出した場合
    elif before.channel and (after.channel is None or before.channel.id != after.channel.id):
        if member in active_members:
            active_members.remove(member)
            # 該当メンバーのEmbedを削除
            if member in last_embed_messages:
                await last_embed_messages[member].delete()
                del last_embed_messages[member]
        if before.channel:
            await post_individual_embeds(before.channel)

bot.run(TOKEN)
