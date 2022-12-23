from dotenv import dotenv_values
from discord.ext import tasks
import discord
from data.commodity import Commodity
from data.arbitrage import arbitrage_finder

CONFIG = dotenv_values(".env")
INTENTS = discord.Intents.default()

bot = discord.Bot()
notifications = [
    Commodity(
        "Low Temperature Diamonds",
        "https://eddb.io/commodity/276",
        True,
        400000,
    )
]


@bot.event
async def on_ready():
    print("Bot is ready.")
    await send_notifications.start()


@tasks.loop(minutes=5)
async def send_notifications():
    guild = bot.guilds[0]
    channel = guild.get_channel(int(CONFIG["CHANNEL_ID"]))
    for notification in notifications:
        if notification.loop() and notification.embed:
            await channel.send("<@&1001604015550890104>", embed=notification.embed)


@bot.slash_command(
    name="arbitragae", description="Calculates the best commodity for arbitrage"
)
async def arbitrage(ctx):
    # await ctx.respond("Determining the best arbitrage location.")
    await ctx.response.defer()
    # await ctx.response.send(embed=arbitrage_finder())
    await ctx.respond(embed=arbitrage_finder())


# client = MyClient(intents=INTENTS)
bot.run(CONFIG["TOKEN"])
