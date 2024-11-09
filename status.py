import discord

client = discord.Client()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.user.set_activity('編纂中', type=discord.ActivityType.custom)

client.run('YOUR_BOT_TOKEN')
