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
# =========================
# Prefix Ping
# =========================
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")
# =========================
# Slash Ping
# =========================
@bot.tree.command(
    name="ping",
    description="Check if the bot is online"
)
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")
# =========================
# CLEAR CHANNEL
# =========================
@bot.tree.command(
    name="clear",
    description="Delete all messages in this channel"
)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True)
    try:
        deleted_count = 0
        # Delete messages in batches.
        # Discord only allows bulk deletion for messages
        # newer than 14 days, so older messages are deleted
        # individually.
        while True:
            messages = [
                message async for message in channel.history(limit=100)
            ]
            if not messages:
                break
            # Separate recent and old messages
            recent_messages = []
            old_messages = []
            for message in messages:
                if message.id:
                    recent_messages.append(message)
            if recent_messages:
                try:
                    await channel.delete_messages(recent_messages)
                    deleted_count += len(recent_messages)
                except discord.HTTPException:
                    # If bulk deletion fails, delete individually
                    for message in recent_messages:
                        try:
                            await message.delete()
                            deleted_count += 1
                        except discord.HTTPException:
                            pass
            if len(messages) < 100:
                break
        await interaction.followup.send(
            f"🧹 Channel cleared! Deleted **{deleted_count} messages**.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I don't have permission to delete messages in this channel.",
            ephemeral=True
        )
    except discord.HTTPException as error:
        print(f"Clear error: {error}")
        await interaction.followup.send(
            "❌ Discord returned an error while clearing the channel.",
            ephemeral=True
        )
# =========================
# SNIPE SCANNER
# =========================
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
# =========================
# Sync Slash Commands
# =========================
@bot.event
async def setup_hook():
    await bot.tree.sync()
# =========================
# Start Discord Bot
# =========================
bot.run(TOKEN)
