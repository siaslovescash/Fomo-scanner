import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands, tasks

from scanner import snipe_scan


# =========================
# Render Web Server
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Discord bot is running!")

    def log_message(self, format, *args):
        return


def start_web_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)

    print(f"WEB SERVER STARTED ON PORT {port}", flush=True)

    server.serve_forever()


web_thread = threading.Thread(
    target=start_web_server,
    daemon=True
)

web_thread.start()


# =========================
# Discord Token
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")


# =========================
# Discord Bot
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# Connection Monitoring
# =========================
@tasks.loop(seconds=30)
async def heartbeat_monitor():
    try:
        latency = bot.latency

        if latency == float("inf"):
            print(
                "BOT HEARTBEAT WARNING | Discord connection not available",
                flush=True
            )
        else:
            print(
                f"BOT HEARTBEAT OK | Latency: {latency * 1000:.0f}ms | "
                f"Ready: {bot.is_ready()} | "
                f"Servers: {len(bot.guilds)}",
                flush=True
            )

    except Exception as error:
        print(
            f"HEARTBEAT MONITOR ERROR: {error}",
            flush=True
        )


@heartbeat_monitor.before_loop
async def before_heartbeat_monitor():
    await bot.wait_until_ready()


# =========================
# Discord Events
# =========================
@bot.event
async def on_connect():
    print("DISCORD CONNECTED TO GATEWAY", flush=True)


@bot.event
async def on_disconnect():
    print("DISCORD DISCONNECTED FROM GATEWAY", flush=True)


@bot.event
async def on_resumed():
    print("DISCORD SESSION RESUMED", flush=True)


@bot.event
async def on_ready():
    print("========================================", flush=True)
    print("BOT IS ONLINE", flush=True)
    print(f"BOT NAME: {bot.user}", flush=True)
    print(f"BOT ID: {bot.user.id}", flush=True)
    print(f"SERVERS: {len(bot.guilds)}", flush=True)

    for guild in bot.guilds:
        print(
            f"SERVER: {guild.name} | ID: {guild.id}",
            flush=True
        )

    print("========================================", flush=True)

    if not heartbeat_monitor.is_running():
        heartbeat_monitor.start()
        print("HEARTBEAT MONITOR STARTED", flush=True)


# =========================
# Interaction Logging
# =========================
@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        command_name = "UNKNOWN"

        if interaction.command:
            command_name = interaction.command.name

        print("========================================", flush=True)
        print("DISCORD INTERACTION RECEIVED", flush=True)
        print(f"TYPE: {interaction.type}", flush=True)
        print(f"COMMAND: /{command_name}", flush=True)
        print(f"USER: {interaction.user}", flush=True)
        print(f"GUILD: {interaction.guild}", flush=True)
        print("========================================", flush=True)

    except Exception as error:
        print(
            f"INTERACTION LOG ERROR: {error}",
            flush=True
        )


# =========================
# Prefix Command
# =========================
@bot.command()
async def ping(ctx):
    print(
        f"PREFIX COMMAND RECEIVED: !ping | USER: {ctx.author}",
        flush=True
    )

    await ctx.send("Pong! 🏓")


# =========================
# /ping
# =========================
@bot.tree.command(
    name="ping",
    description="Check if the bot is online"
)
async def slash_ping(interaction: discord.Interaction):

    print(
        "SLASH COMMAND RUNNING: /ping",
        flush=True
    )

    await interaction.response.send_message(
        "Pong! 🏓"
    )


# =========================
# /clear
# =========================
@bot.tree.command(
    name="clear",
    description="Delete all messages in this channel"
)
@discord.app_commands.checks.has_permissions(
    manage_messages=True
)
async def clear(interaction: discord.Interaction):

    print(
        f"SLASH COMMAND RUNNING: /clear | USER: {interaction.user}",
        flush=True
    )

    channel = interaction.channel

    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )
        return

    await interaction.response.defer(
        ephemeral=True
    )

    try:
        deleted = await channel.purge(
            limit=None,
            bulk=True
        )

        print(
            f"CLEAR FINISHED | DELETED: {len(deleted)}",
            flush=True
        )

        await interaction.followup.send(
            f"🧹 Deleted {len(deleted)} messages.",
            ephemeral=True
        )

    except Exception as error:

        print(
            f"CLEAR ERROR: {error}",
            flush=True
        )

        await interaction.followup.send(
            "❌ I couldn't clear the messages.",
            ephemeral=True
        )


# =========================
# /snipe
# =========================
@bot.tree.command(
    name="snipe",
    description="Scan for newly detected coins"
)
async def snipe(interaction: discord.Interaction):

    print(
        "SLASH COMMAND RUNNING: /snipe",
        flush=True
    )

    await interaction.response.defer()

    try:

        print(
            "STARTING SNIPE SCANNER...",
            flush=True
        )

        coins = await snipe_scan()

        print(
            f"SNIPE SCANNER FINISHED | RESULTS: "
            f"{len(coins) if coins else 0}",
            flush=True
        )

        if not coins:
            await interaction.followup.send(
                "No coins found."
            )
            return

        message = ""

        for coin in coins:

            line = str(coin) + "\n"

            if len(message) + len(line) > 1900:

                await interaction.followup.send(
                    message
                )

                message = ""

            message += line

        if message:

            await interaction.followup.send(
                message
            )

    except Exception as error:

        print(
            f"SNIPE ERROR: {error}",
            flush=True
        )

        await interaction.followup.send(
            "❌ The scanner encountered an error. "
            "Check the Render logs."
        )


# =========================
# Slash Command Errors
# =========================
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):

    print("========================================", flush=True)
    print("SLASH COMMAND ERROR", flush=True)
    print(
        f"ERROR TYPE: {type(error).__name__}",
        flush=True
    )
    print(
        f"ERROR: {error}",
        flush=True
    )
    print("========================================", flush=True)


# =========================
# Sync Commands
# =========================
@bot.event
async def setup_hook():

    print("========================================", flush=True)
    print("SYNCING SLASH COMMANDS...", flush=True)
    print("========================================", flush=True)

    try:

        synced = await bot.tree.sync()

        print(
            f"SYNCED {len(synced)} SLASH COMMAND(S)",
            flush=True
        )

        for command in synced:

            print(
                f"REGISTERED: /{command.name}",
                flush=True
            )

    except Exception as error:

        print(
            f"SLASH COMMAND SYNC ERROR: {error}",
            flush=True
        )


# =========================
# Start Bot
# =========================
print("========================================", flush=True)
print("STARTING DISCORD BOT...", flush=True)
print("========================================", flush=True)

bot.run(TOKEN)
