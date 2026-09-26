import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands, tasks

from scanner import snipe_scan, websitecoins_scan


# ============================================================
# GLOBAL STATE
# ============================================================

START_TIME = time.time()
LAST_SOCKET_EVENT = time.time()
LAST_INTERACTION = 0
GATEWAY_CONNECTED = False

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    enable_debug_events=True
)


# ============================================================
# SOCKET ACTIVITY
# ============================================================

def mark_socket_activity():
    global LAST_SOCKET_EVENT
    LAST_SOCKET_EVENT = time.time()


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            uptime = int(time.time() - START_TIME)

            if bot.is_ready() and GATEWAY_CONNECTED:
                gateway_status = "CONNECTED"
            else:
                gateway_status = "DISCONNECTED"

            ws = getattr(bot, "ws", None)

            if ws is None:
                websocket_status = "NONE"
            else:
                try:
                    websocket_status = (
                        "CLOSED"
                        if ws.is_closed()
                        else "OPEN"
                    )
                except Exception:
                    websocket_status = "UNKNOWN"

            body = (
                "Discord bot is running!\n"
                f"Uptime: {uptime}s\n"
                f"Gateway: {gateway_status}\n"
                f"WebSocket: {websocket_status}\n"
                f"Bot Ready: {bot.is_ready()}\n"
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
                "HEALTH SERVER ERROR | "
                f"{type(error).__name__} | {error}",
                flush=True
            )

    def log_message(self, format, *args):
        return


def start_web_server():
    try:
        port = int(os.getenv("PORT", "10000"))

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
# DISCORD GATEWAY EVENTS
# ============================================================

@bot.event
async def on_connect():
    global GATEWAY_CONNECTED

    GATEWAY_CONNECTED = True
    mark_socket_activity()

    print(
        "========================================",
        flush=True
    )

    print(
        "EVENT: DISCORD CONNECTED TO GATEWAY",
        flush=True
    )

    print(
        "GATEWAY STATE: CONNECTED",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )


@bot.event
async def on_disconnect():
    global GATEWAY_CONNECTED

    GATEWAY_CONNECTED = False

    print(
        "========================================",
        flush=True
    )

    print(
        "EVENT: DISCORD DISCONNECTED FROM GATEWAY",
        flush=True
    )

    print(
        "GATEWAY STATE: DISCONNECTED",
        flush=True
    )

    print(
        "DISCORD.PY WILL ATTEMPT TO RECONNECT",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )


@bot.event
async def on_resumed():
    global GATEWAY_CONNECTED

    GATEWAY_CONNECTED = True
    mark_socket_activity()

    print(
        "========================================",
        flush=True
    )

    print(
        "EVENT: DISCORD SESSION RESUMED",
        flush=True
    )

    print(
        "GATEWAY STATE: CONNECTED",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )


# ============================================================
# RAW SOCKET EVENT DIAGNOSTIC
# ============================================================

@bot.event
async def on_socket_event_type(event_type):

    mark_socket_activity()

    important_events = {
        "READY",
        "RESUMED",
        "INTERACTION_CREATE",
        "MESSAGE_CREATE",
        "GUILD_CREATE",
        "HEARTBEAT_ACK",
    }

    if event_type in important_events:
        print(
            f"SOCKET EVENT | {event_type}",
            flush=True
        )


# ============================================================
# RAW SOCKET RECEIVE DIAGNOSTIC
# ============================================================

@bot.event
async def on_socket_raw_receive(payload):

    mark_socket_activity()

    try:

        if isinstance(payload, str):

            if '"t":"INTERACTION_CREATE"' in payload:
                print(
                    "RAW SOCKET EVENT | INTERACTION_CREATE RECEIVED",
                    flush=True
                )

    except Exception as error:

        print(
            "RAW SOCKET RECEIVE ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    mark_socket_activity()

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
        "GATEWAY STATE: CONNECTED",
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

        ws = getattr(bot, "ws", None)

        if ws is None:

            websocket_state = "NONE"

        else:

            try:

                websocket_state = (
                    "CLOSED"
                    if ws.is_closed()
                    else "OPEN"
                )

            except Exception:

                websocket_state = "UNKNOWN"

        connected = (
            bot.is_ready()
            and GATEWAY_CONNECTED
            and websocket_state == "OPEN"
        )

        state = (
            "CONNECTED"
            if connected
            else "DISCONNECTED"
        )

        socket_idle = (
            time.time() - LAST_SOCKET_EVENT
        )

        interaction_age = (
            "NEVER"
            if LAST_INTERACTION == 0
            else f"{time.time() - LAST_INTERACTION:.0f}s"
        )

        print(
            "GATEWAY STATUS | "
            f"State={state} | "
            f"Ready={bot.is_ready()} | "
            f"WebSocket={websocket_state} | "
            f"Latency={bot.latency * 1000:.0f}ms | "
            f"Guilds={len(bot.guilds)} | "
            f"SocketIdle={socket_idle:.0f}s | "
            f"LastInteraction={interaction_age} | "
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

        ws = getattr(bot, "ws", None)

        if ws is None:

            websocket_state = "NONE"

        else:

            try:

                websocket_state = (
                    "CLOSED"
                    if ws.is_closed()
                    else "OPEN"
                )

            except Exception:

                websocket_state = "UNKNOWN"

        print(
            "WATCHDOG | "
            f"Ready={bot.is_ready()} | "
            f"GatewayConnected={GATEWAY_CONNECTED} | "
            f"WebSocket={websocket_state} | "
            f"User={bot.user}",
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

    global LAST_INTERACTION

    LAST_INTERACTION = time.time()

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

        await ctx.send("Pong! 🏓")

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

    if not isinstance(channel, discord.TextChannel):

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


# ============================================================
# MONEY FORMAT
# ============================================================

def format_money(value):

    try:

        value = float(value)

    except Exception:

        return "$0"

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"${value / 1_000:.1f}K"

    return f"${value:.2f}"


# ============================================================
# COIN EMBED
# ============================================================

def create_coin_embed(coin, number, mode="snipe"):

    name = coin.get("name", "Unknown")
    symbol = coin.get("symbol", "???")

    chain_name = coin.get(
        "chain_name",
        coin.get("chain", "Unknown")
    )

    market_cap = coin.get(
        "market_cap",
        0
    )

    liquidity = coin.get(
        "liquidity",
        0
    )

    volume = coin.get(
        "volume_24h",
        0
    )

    address = coin.get(
        "address",
        "Unknown"
    )

    created_time = coin.get(
        "created_time",
        "Unknown"
    )

    age = coin.get(
        "age",
        "Unknown"
    )

    fomo_url = coin.get(
        "fomo_url"
    )

    bubblemaps_url = coin.get(
        "bubblemaps"
    )

    website = coin.get(
        "website"
    )

    embed = discord.Embed(
        title=f"🪙 #{number} {name} ({symbol})",
        description=f"**{chain_name}**",
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="💰 Market Cap",
        value=format_money(market_cap),
        inline=True
    )

    embed.add_field(
        name="💧 Liquidity",
        value=format_money(liquidity),
        inline=True
    )

    embed.add_field(
        name="📊 24h Volume",
        value=format_money(volume),
        inline=True
    )

    embed.add_field(
        name="🕐 Creation Time",
        value=str(created_time),
        inline=True
    )

    embed.add_field(
        name="⏱️ Running Time",
        value=str(age),
        inline=True
    )

    embed.add_field(
        name="🔗 Contract",
        value=f"`{address}`",
        inline=False
    )

    if fomo_url:

        embed.add_field(
            name="🔥 FOMO",
            value=f"[Open Coin in FOMO]({fomo_url})",
            inline=True
        )

    if bubblemaps_url:

        embed.add_field(
            name="🫧 Bubblemaps",
            value=f"[View Map]({bubblemaps_url})",
            inline=True
        )

    if mode == "website" and website:

        embed.add_field(
            name="🌐 Website",
            value=f"[Open Website]({website})",
            inline=False
        )

    embed.set_footer(
        text=(
            "FOMO Website Coins"
            if mode == "website"
            else "FOMO Snipe"
        )
    )

    return embed


# ============================================================
# SEND COIN RESULTS
# ============================================================

async def send_coin_results(
    interaction,
    coins,
    title,
    mode="snipe"
):

    if not coins:

        await interaction.followup.send(
            "No qualifying coins found."
        )

        return

    # Discord allows a maximum of 10 embeds
    # in one message.
    for start in range(
        0,
        len(coins),
        10
    ):

        batch = coins[
            start:start + 10
        ]

        embeds = []

        for index, coin in enumerate(
            batch,
            start=start + 1
        ):

            embeds.append(
                create_coin_embed(
                    coin,
                    index,
                    mode
                )
            )

        content = None

        if start == 0:

            content = title

        await interaction.followup.send(
            content=content,
            embeds=embeds
        )


# ============================================================
# /SNIPE
# ============================================================

@bot.tree.command(
    name="snipe",
    description="Scan for newly detected Solana and Robinhood Chain coins"
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

        await send_coin_results(
            interaction,
            coins,
            "🔥 **FOMO SNIPE — SOLANA + ROBINHOOD CHAIN**",
            "snipe"
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
# /WEBSITECOINS
# ============================================================

@bot.tree.command(
    name="websitecoins",
    description="Find Solana and Robinhood Chain coins with websites"
)
async def websitecoins(interaction):

    print(
        f"COMMAND: /websitecoins | USER={interaction.user}",
        flush=True
    )

    try:

        await interaction.response.defer()

    except Exception as error:

        print(
            "WEBSITECOINS DEFER ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

        return

    try:

        print(
            "WEBSITE COIN SCANNER STARTING",
            flush=True
        )

        coins = await websitecoins_scan()

        print(
            "WEBSITE COIN SCANNER FINISHED | "
            f"RESULTS={len(coins) if coins else 0}",
            flush=True
        )

        await send_coin_results(
            interaction,
            coins,
            "🌐 **FOMO WEBSITE COINS — SOLANA + ROBINHOOD CHAIN**",
            "website"
        )

    except Exception as error:

        print(
            "WEBSITECOINS ERROR | "
            f"{type(error).__name__} | {error}",
            flush=True
        )

        try:

            await interaction.followup.send(
                "❌ The website coin scanner encountered an error. "
                "Check the Render logs."
            )

        except Exception as followup_error:

            print(
                "WEBSITECOINS FOLLOWUP ERROR | "
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
    "WEBSOCKET DIAGNOSTICS: ENABLED",
    flush=True
)

print(
    "FOMO SCANNER: ENABLED",
    flush=True
)

print(
    "TARGET CHAINS: SOLANA + ROBINHOOD",
    flush=True
)

print(
    "TARGET RESULTS: 10 SOLANA + 10 ROBINHOOD",
    flush=True
)

print(
    "COMMANDS: /ping /clear /snipe /websitecoins",
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
