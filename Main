import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}! 👋")


@bot.command()
async def helpme(ctx):
    await ctx.send(
        "**FOMO Bot Commands**\n"
        "`!ping` - Check if the bot is working\n"
        "`!hello` - Say hello\n"
        "`!helpme` - Show this help message"
    )


bot.run(TOKEN)
