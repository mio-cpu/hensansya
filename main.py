import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境変数を読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN が設定されていません。'.env' ファイルを確認してください。")

# 必要なインテントの設定
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 非活動日数のデフォルト設定
DEFAULT_INACTIVITY_DAYS = 30
inactivity_days = DEFAULT_INACTIVITY_DAYS


class InactivityManager(commands.Cog):
    """非活動メンバーを管理するコグ"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_inactivity_days", description="非活動日数を設定します")
    async def set_inactivity_days(self, interaction: discord.Interaction, days: int):
        """非活動日数を設定するスラッシュコマンド"""
        global inactivity_days
        inactivity_days = days
        await interaction.response.send_message(f"非活動日数を {days} 日に設定しました！", ephemeral=True)

    @app_commands.command(name="get_inactivity_days", description="現在の非活動日数を確認します")
    async def get_inactivity_days(self, interaction: discord.Interaction):
        """現在の非活動日数を確認するスラッシュコマンド"""
        await interaction.response.send_message(f"現在の非活動日数は {inactivity_days} 日です。", ephemeral=True)

    @app_commands.command(name="check_inactive_members", description="非活動メンバーを確認します")
    async def check_inactive_members(self, interaction: discord.Interaction):
        """非活動メンバーを確認するスラッシュコマンド"""
        guild = interaction.guild
        now = datetime.utcnow()
        inactive_threshold = now - timedelta(days=inactivity_days)
        inactive_members = []

        for member in guild.members:
            if member.bot:  # ボットはスキップ
                continue

            last_message_time = await self.get_last_message_time(member, guild)
            if last_message_time is None or last_message_time < inactive_threshold:
                inactive_members.append(member)

        # 結果を送信
        if inactive_members:
            message = "以下のメンバーが非活動です:\n" + "\n".join([member.name for member in inactive_members])
        else:
            message = "非活動のメンバーはいません。"
        await interaction.response.send_message(message)

    @staticmethod
    async def get_last_message_time(member: discord.Member, guild: discord.Guild):
        """メンバーの最後のメッセージ時刻を取得"""
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=1000):
                    if message.author == member:
                        return message.created_at
            except discord.Forbidden:
                continue  # 権限がないチャンネルをスキップ
        return None


@bot.event
async def on_ready():
    """Bot の準備完了時の処理"""
    logger.info("Bot is ready")
    logger.info(f"Connected to the following guilds: {[guild.name for guild in bot.guilds]}")

    # スラッシュコマンドの同期
    try:
        synced = await bot.tree.sync()
        logger.info(f"スラッシュコマンドが {len(synced)} 個グローバルに同期されました。")
    except Exception as e:
        logger.error(f"スラッシュコマンドの同期中にエラーが発生しました: {e}")


async def setup_hook():
    """Bot のセットアップ時に Cog を登録"""
    await bot.add_cog(InactivityManager(bot))


# Bot にセットアップフックを登録
bot.setup_hook = setup_hook

# ボットを実行
bot.run(TOKEN)
