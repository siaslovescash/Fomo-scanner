import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands, tasks

from scanner import snipe_scan


# =========================
# Render Health Server
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

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"WEB SERVER STARTED ON PORT {port}",
        flush=True
    )

    server.serve_forever()


threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# =========================
# Discord Token
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")


# =========================
# Discord Intents
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# Gateway Monitor
# =========================
@tasks.loop(seconds=30)
async def gateway_monitor():

    try:

        latency = bot.latency

        print(
            "GATEWAY STATUS | "
            f"Ready={bot.is_ready()} | "
            f"Latency={latency * 1000:.0f}ms | "
            f"Guilds={len(bot.guilds)} | "
            f"User={bot.user}",
            flush=True
        )

    except Exception as error:

        print(
            f"GATEWAY MONITOR ERROR | {error}",
            flush=True
        )


@gateway_monitor.before_loop
async def before_gateway_monitor():

    await bot.wait_until_ready()


# =========================
# Gateway Events
# =========================
@bot.event
async def on_connect():

    print(
        "EVENT: DISCORD CONNECTED TO GATEWAY",
        flush=True
    )


@bot.event
async def on_disconnect():

    print(
        "EVENT: DISCORD DISCONNECTED FROM GATEWAY",
        flush=True
    )


@bot.event
async def on_resumed():

    print(
        "EVENT: DISCORD SESSION RESUMED",
        flush=True
    )


# =========================
# Ready
# =========================
@bot.event
async def on_ready():

    print("========================================", flush=True)

    print(
        "EVENT: BOT READY",
        flush=True
    )

    print(
        f"BOT: {bot.user}",
        flush=True
    )

    print(
        f"BOT ID: {bot.user.id}",
        flush=True
    )

    print(
        f"GUILDS: {len(bot.guilds)}",
        flush=True
    )

    for guild in bot.guilds:

        print(
            f"GUILD: {guild.name} | {guild.id}",
            flush=True
        )

    print("========================================", flush=True)

    if not gateway_monitor.is_running():

        gateway_monitor.start()

        print(
            "GATEWAY MONITOR STARTED",
            flush=True
        )


# =========================
# MESSAGE EVENT MONITOR
# =========================
@bot.event
async def on_message(message):

    try:

        if message.author.bot:
            return

        print(
            "EVENT: MESSAGE RECEIVED | "
            f"USER={message.author} | "
            f"CHANNEL={message.channel} | "
            f"CONTENT={message.content[:100]}",
            flush=True
        )

        await bot.process_commands(message)

    except Exception as error:

        print(
            f"MESSAGE EVENT ERROR | {error}",
            flush=True
        )


# =========================
# INTERACTION MONITOR
# =========================
@bot.event
async def on_interaction(interaction):

    try:

        command_name = "UNKNOWN"

        if interaction.command:
            command_name = interaction.command.name

        print(
            "EVENT: INTERACTION RECEIVED | "
            f"TYPE={interaction.type} | "
            f"COMMAND=/{command_name} | "
            f"USER={interaction.user}",
            flush=True
        )

    except Exception as error:

        print(
            f"INTERACTION EVENT ERROR | {error}",
            flush=True
        )


# =========================
# !ping
# =========================
@bot.command()
async def ping(ctx):

    print(
        f"COMMAND: !ping | USER={ctx.author}",
        flush=True
    )

    try:

        await ctx.send("Pong! 🏓")

        print(
            "PING RESPONSE SENT | TYPE=PREFIX",
            flush=True
        )

    except Exception as error:

        print(
            f"PING RESPONSE ERROR | TYPE=PREFIX | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


# =========================
# /ping
# =========================
@bot.tree.command(
    name="ping",
    description="Check if the bot is online"
)
async def slash_ping(interaction: discord.Interaction):

    print(
        f"COMMAND: /ping | USER={interaction.user}",
        flush=True
    )

    print(
        f"PING STATE | "
        f"Responded={interaction.response.is_done()} | "
        f"Guild={interaction.guild} | "
        f"Channel={interaction.channel}",
        flush=True
    )

    try:

        await interaction.response.send_message(
            "Pong! 🏓"
        )

        print(
            "PING RESPONSE SENT | TYPE=SLASH",
            flush=True
        )

    except Exception as error:

        print(
            "PING RESPONSE ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

        # Try a follow-up if Discord already considers
        # the interaction acknowledged.
        try:

            if interaction.response.is_done():

                await interaction.followup.send(
                    "Pong! 🏓"
                )

                print(
                    "PING FOLLOWUP RESPONSE SENT",
                    flush=True
                )

        except Exception as followup_error:

            print(
                "PING FOLLOWUP ERROR | "
                f"{type(followup_error).__name__} | "
                f"{followup_error}",
                flush=True
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
        f"COMMAND: /clear | USER={interaction.user}",
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
            f"CLEAR COMPLETE | DELETED={len(deleted)}",
            flush=True
        )

        await interaction.followup.send(
            f"🧹 Deleted {len(deleted)} messages.",
            ephemeral=True
        )

    except Exception as error:

        print(
            f"CLEAR ERROR | {error}",
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
        "COMMAND: /snipe",
        flush=True
    )

    await interaction.response.defer()

    try:

        print(
            "SNIPE SCANNER STARTING",
            flush=True
        )

        coins = await snipe_scan()

        print(
            f"SNIPE SCANNER FINISHED | "
            f"RESULTS={len(coins) if coins else 0}",
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
            f"SNIPE ERROR | {error}",
            flush=True
        )

        try:

            await interaction.followup.send(
                "❌ The scanner encountered an error. "
                "Check the Render logs."
            )

        except Exception as followup_error:

            print(
                f"SNIPE FOLLOWUP ERROR | {followup_error}",
                flush=True
            )


# =========================
# Slash Command Errors
# =========================
@bot.tree.error
async def on_app_command_error(
    interaction,
    error
):

    print(
        "========================================",
        flush=True
    )

    print(
        f"SLASH COMMAND ERROR | "
        f"{type(error).__name__} | {error}",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                "❌ Command error. Check the Render logs.",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                "❌ Command error. Check the Render logs.",
                ephemeral=True
            )

    except Exception as response_error:

        print(
            f"COMMAND ERROR RESPONSE FAILED | "
            f"{type(response_error).__name__} | "
            f"{response_error}",
            flush=True
        )


# =========================
# Sync Slash Commands
# =========================
@bot.event
async def setup_hook():

    print(
        "SYNCING SLASH COMMANDS...",
        flush=True
    )

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
            f"SLASH COMMAND SYNC ERROR | {error}",
            flush=True
        )


# =========================
# Start
# =========================
print(
    "STARTING DISCORD BOT...",
    flush=True
)

bot.run(TOKEN)
