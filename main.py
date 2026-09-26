import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands, tasks

from scanner import snipe_scan


# ============================================================
# GLOBAL STATE
# ============================================================

START_TIME = time.time()
LAST_GATEWAY_ACTIVITY = time.time()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")


# ============================================================
# DISCORD INTENTS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# GATEWAY ACTIVITY
# ============================================================

def mark_gateway_activity():
    global LAST_GATEWAY_ACTIVITY
    LAST_GATEWAY_ACTIVITY = time.time()


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            uptime = int(time.time() - START_TIME)

            if bot.is_ready():
                gateway_status = "True"
            else:
                gateway_status = "False"

            body = (
                "Discord bot is running!\n"
                f"Uptime: {uptime}s\n"
                f"Gateway ready: {gateway_status}\n"
                f"Bot: {bot.user}\n"
            )

            body_bytes = body.encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body_bytes))
            )
            self.end_headers()

            self.wfile.write(body_bytes)

        except Exception as error:

            print(
                f"HEALTH SERVER ERROR | "
                f"{type(error).__name__} | {error}",
                flush=True
            )

    def log_message(self, format, *args):
        return


def start_web_server():

    try:

        port = int(
            os.getenv(
                "PORT",
                "10000"
            )
        )

        server = HTTPServer(
            ("0.0.0.0", port),
            HealthHandler
        )

        print(
            f"WEB SERVER STARTED | PORT={port}",
            flush=True
        )

        server.serve_forever()

    except Exception as error:

        print(
            "WEB SERVER FATAL ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


web_thread = threading.Thread(
    target=start_web_server,
    daemon=True
)

web_thread.start()


# ============================================================
# GATEWAY EVENTS
# ============================================================

@bot.event
async def on_connect():

    mark_gateway_activity()

    print(
        "EVENT: DISCORD CONNECTED TO GATEWAY",
        flush=True
    )


@bot.event
async def on_disconnect():

    mark_gateway_activity()

    print(
        "EVENT: DISCORD DISCONNECTED FROM GATEWAY",
        flush=True
    )


@bot.event
async def on_resumed():

    mark_gateway_activity()

    print(
        "EVENT: DISCORD SESSION RESUMED",
        flush=True
    )


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():

    mark_gateway_activity()

    print(
        "========================================",
        flush=True
    )

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

    print(
        "========================================",
        flush=True
    )

    if not gateway_monitor.is_running():

        gateway_monitor.start()

        print(
            "GATEWAY MONITOR STARTED",
            flush=True
        )


# ============================================================
# GATEWAY MONITOR
# ============================================================

@tasks.loop(seconds=30)
async def gateway_monitor():

    try:

        mark_gateway_activity()

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
            "GATEWAY MONITOR ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


@gateway_monitor.before_loop
async def before_gateway_monitor():

    await bot.wait_until_ready()


# ============================================================
# CONNECTION WATCHDOG
# ============================================================

@tasks.loop(seconds=60)
async def connection_watchdog():

    try:

        now = time.time()

        idle_seconds = (
            now - LAST_GATEWAY_ACTIVITY
        )

        print(
            "WATCHDOG | "
            f"Ready={bot.is_ready()} | "
            f"GatewayIdle={idle_seconds:.0f}s | "
            f"User={bot.user}",
            flush=True
        )

        if not bot.is_ready():

            print(
                "WATCHDOG WARNING | "
                "Discord Gateway is not ready.",
                flush=True
            )

    except Exception as error:

        print(
            "WATCHDOG ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


@connection_watchdog.before_loop
async def before_connection_watchdog():

    await bot.wait_until_ready()


# ============================================================
# MESSAGE EVENT
# ============================================================

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
            "MESSAGE EVENT ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


# ============================================================
# INTERACTION MONITOR
# ============================================================

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
            "INTERACTION EVENT ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


# ============================================================
# !PING
# ============================================================

@bot.command()
async def ping(ctx):

    print(
        f"COMMAND: !ping | USER={ctx.author}",
        flush=True
    )

    try:

        await ctx.send(
            "Pong! 🏓"
        )

        print(
            "PING RESPONSE SENT | TYPE=PREFIX",
            flush=True
        )

    except Exception as error:

        print(
            "PING RESPONSE ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


# ============================================================
# /PING
# ============================================================

@bot.tree.command(
    name="ping",
    description="Check if the bot is online"
)
async def slash_ping(interaction):

    print(
        f"COMMAND: /ping | USER={interaction.user}",
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

        try:

            if interaction.response.is_done():

                await interaction.followup.send(
                    "Pong! 🏓"
                )

        except Exception as followup_error:

            print(
                "PING FOLLOWUP ERROR | "
                f"{type(followup_error).__name__} | "
                f"{followup_error}",
                flush=True
            )


# ============================================================
# /CLEAR
# ============================================================

@bot.tree.command(
    name="clear",
    description="Delete all messages in this channel"
)
@discord.app_commands.checks.has_permissions(
    manage_messages=True
)
async def clear(interaction):

    print(
        f"COMMAND: /clear | USER={interaction.user}",
        flush=True
    )

    channel = interaction.channel

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )

        return

    try:

        await interaction.response.defer(
            ephemeral=True
        )

        print(
            "CLEAR STARTING",
            flush=True
        )

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

        print(
            "CLEAR RESPONSE SENT",
            flush=True
        )

    except Exception as error:

        print(
            "CLEAR ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

        try:

            if interaction.response.is_done():

                await interaction.followup.send(
                    "❌ I couldn't clear the messages.",
                    ephemeral=True
                )

            else:

                await interaction.response.send_message(
                    "❌ I couldn't clear the messages.",
                    ephemeral=True
                )

        except Exception as response_error:

            print(
                "CLEAR ERROR RESPONSE FAILED | "
                f"{type(response_error).__name__} | "
                f"{response_error}",
                flush=True
            )


# ============================================================
# /SNIPE
# ============================================================

@bot.tree.command(
    name="snipe",
    description="Scan for newly detected coins"
)
async def snipe(interaction):

    print(
        f"COMMAND: /snipe | USER={interaction.user}",
        flush=True
    )

    try:

        await interaction.response.defer()

    except Exception as error:

        print(
            "SNIPE DEFER ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

        return

    try:

        print(
            "SNIPE SCANNER STARTING",
            flush=True
        )

        coins = await snipe_scan()

        print(
            "SNIPE SCANNER FINISHED | "
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
            "SNIPE ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

        try:

            await interaction.followup.send(
                "❌ The scanner encountered an error. "
                "Check the Render logs."
            )

        except Exception as followup_error:

            print(
                "SNIPE FOLLOWUP ERROR | "
                f"{type(followup_error).__name__} | "
                f"{followup_error}",
                flush=True
            )


# ============================================================
# SLASH COMMAND ERROR HANDLER
# ============================================================

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
        "SLASH COMMAND ERROR | "
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
            "COMMAND ERROR RESPONSE FAILED | "
            f"{type(response_error).__name__} | "
            f"{response_error}",
            flush=True
        )


# ============================================================
# SYNC SLASH COMMANDS
# ============================================================

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
            "SLASH COMMAND SYNC ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

    if not connection_watchdog.is_running():

        connection_watchdog.start()

        print(
            "CONNECTION WATCHDOG STARTED",
            flush=True
        )


# ============================================================
# PROCESS SIGNAL HANDLERS
# ============================================================

def shutdown_signal_handler(
    signum,
    frame
):

    signal_name = signal.Signals(
        signum
    ).name

    print(
        "========================================",
        flush=True
    )

    print(
        "PROCESS SHUTDOWN SIGNAL RECEIVED",
        flush=True
    )

    print(
        f"SIGNAL={signum} ({signal_name})",
        flush=True
    )

    print(
        "IMPORTANT: The hosting platform requested "
        "the process to stop.",
        flush=True
    )

    print(
        "This was NOT caused by /clear.",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )


try:

    signal.signal(
        signal.SIGTERM,
        shutdown_signal_handler
    )

    signal.signal(
        signal.SIGINT,
        shutdown_signal_handler
    )

except Exception as error:

    print(
        "SIGNAL HANDLER SETUP ERROR | "
        f"{type(error).__name__} | {error}",
        flush=True
    )


# ============================================================
# START BOT
# ============================================================

print(
    "========================================",
    flush=True
)

print(
    "STARTING DISCORD BOT...",
    flush=True
)

print(
    f"PYTHON PID: {os.getpid()}",
    flush=True
)

print(
    f"START TIME: {time.time()}",
    flush=True
)

print(
    "RENDER HEALTH SERVER: ENABLED",
    flush=True
)

print(
    "DISCORD RECONNECT: ENABLED",
    flush=True
)

print(
    "========================================",
    flush=True
)


try:

    bot.run(
        TOKEN,
        reconnect=True
    )

except KeyboardInterrupt:

    print(
        "BOT STOPPED BY KEYBOARD INTERRUPT",
        flush=True
    )

except Exception as error:

    print(
        "FATAL BOT ERROR | "
        f"{type(error).__name__} | {error}",
        flush=True
    )

    raise

finally:

    print(
        "BOT PROCESS EXITING",
        flush=True
    )
