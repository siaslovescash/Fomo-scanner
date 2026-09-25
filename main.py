import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands

from scanner import snipe_scan


# =========================
# Render Web Server
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Discord bot is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Web server listening on port {port}")
    server.serve_forever()


# Start the web server in the background
web_thread = threading.Thread(target=start_web_server, daemon=True)
web_thread.start()


# =========================
# Discord Bot
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@bot.tree.command(
    name="ping",
    description="Check if the bot is online"
)
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")


@bot.tree.command(
    name="snipe",
    description="Scan for newly detected coins"
)
async def snipe(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        coins = await snipe_scan()

        if not coins:
            await interaction.followup.send(
                "🔎 No matching coins found right now."
            )
            return

        message = "**🎯 FOMO SNIPE SCANNER**\n\n"

        for coin in coins:
            name = coin.get("name", "Unknown")
            symbol = coin.get("symbol", "???")
            chain = coin.get("chain", "Unknown")
            market_cap = coin.get("market_cap", 0)
            liquidity = coin.get("liquidity", 0)
            volume = coin.get("volume_24h", 0)
            age = coin.get("age", "Unknown")
            address = coin.get("address", "Unknown")
            url = coin.get("url")
            bubble_url = coin.get("bubblemaps")

            message += (
                f"🪙 **{name} ({symbol})**\n"
                f"⛓️ Chain: **{chain}**\n"
                f"💰 Market Cap: **${market_cap:,.0f}**\n"
                f"💧 Liquidity: **${liquidity:,.0f}**\n"
                f"📈 24h Volume: **${volume:,.0f}**\n"
                f"🕐 Live for: **{age}**\n"
                f"📍 Contract: `{address}`\n"
            )

            if url:
                message += f"🔗 [Coin / Chart]({url})\n"

            if bubble_url:
                message += f"🫧 [Bubblemaps]({bubble_url})\n"

            message += "\n"

        # Discord messages cannot exceed 2,000 characters.
        if len(message) <= 2000:
            await interaction.followup.send(message)
        else:
            chunks = []
            current = ""

            for line in message.splitlines(keepends=True):
                if len(current) + len(line) > 1900:
                    chunks.append(current)
                    current = line
                else:
                    current += line

            if current:
                chunks.append(current)

            for chunk in chunks:
                await interaction.followup.send(chunk)

    except Exception as error:
        print(f"Snipe error: {error}")

        await interaction.followup.send(
            "❌ The scanner encountered an error. "
            "Check the Render logs."
        )


@bot.event
async def setup_hook():
    await bot.tree.sync()


# =========================
# Start Discord Bot
# =========================
bot.run(TOKEN)
