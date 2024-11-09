import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')
SECRET_ROLE_NAME = "秘密のロール"

# サーバーごとの自己紹介チャンネルIDを保存する辞書
server_intro_channels = {}
joined_members_introductions = {}
member_message_ids = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()  # スラッシュコマンドの同期

@bot.tree.command(name="set_intro_channel", description="自己紹介用チャンネルを設定します")
async def set_intro_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    server_intro_channels[interaction.guild.id] = channel.id
    await interaction.response.send_message(f"自己紹介チャンネルが {channel.mention} に設定されました！", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot or before.channel == after.channel or any(role.name == SECRET_ROLE_NAME for role in member.roles):
        return

    intro_channel_id = server_intro_channels.get(member.guild.id)
    if not intro_channel_id:
        return  # 自己紹介チャンネルが未設定の場合、処理を中断

    intro_channel = bot.get_channel(intro_channel_id)

    if before.channel is None and after.channel is not None:
        introduction = None
        async for message in intro_channel.history(limit=500):
            if message.author == member:
                introduction = message.content
                break

        intro_text = introduction if introduction else "自己紹介が見つかりませんでした。"
        joined_members_introductions[member] = intro_text

        embed = discord.Embed(title=f"{member.display_name}さんの自己紹介", description=intro_text, color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url)
        sent_message = await after.channel.send(embed=embed)
        
        member_message_ids[member] = sent_message.id

    elif before.channel is not None and after.channel is None:
        joined_members_introductions.pop(member, None)

        if member in member_message_ids:
            message_id = member_message_ids.pop(member)
            message = await before.channel.fetch_message(message_id)
            await message.delete()

bot.run(TOKEN)
