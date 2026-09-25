import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import discord
from discord.ext import commands
from scanner import snipe_scan
# =========================================================
# RENDER WEB SERVER
# =========================================================
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
    print(f"WEB SERVER STARTED ON PORT {port}", flush=True)
    server.serve_forever()


web_thread = threading.Thread(
    target=start_web_server,
    daemon=True
)
web_thread.start()
# =========================================================
# DISCORD BOT
# =========================================================
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
# =========================================================
# DISCORD CONNECTION EVENTS
# =========================================================
@bot.event
async def on_connect():
    print(
        "DISCORD CONNECTED TO GATEWAY",
        flush=True
    )


@bot.event
async def on_disconnect():
    print(
        "DISCORD DISCONNECTED FROM GATEWAY",
        flush=True
    )


@bot.event
async def on_resumed():
    print(
        "DISCORD SESSION RESUMED",
        flush=True
    )


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
# =========================================================
# GLOBAL INTERACTION LOGGER
# =========================================================
@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        command_name = "UNKNOWN"
        if interaction.command:
            command_name = interaction.command.name
        print(
            "========================================",
            flush=True
        )
        print(
            "DISCORD INTERACTION RECEIVED",
            flush=True
        )
        print(
            f"TYPE: {interaction.type}",
            flush=True
        )
        print(
            f"COMMAND: /{command_name}",
            flush=True
        )
        print(
            f"USER: {interaction.user}",
            flush=True
        )
        print(
            f"GUILD: {interaction.guild}",
            flush=True
        )
        print(
            "========================================",
            flush=True
        )
    except Exception as error:
        print(
            f"INTERACTION LOG ERROR: {error}",
            flush=True
        )
# =========================================================
# PREFIX PING
# =========================================================
@bot.command()
async def ping(ctx):
    print(
        f"PREFIX COMMAND RECEIVED: !ping | USER: {ctx.author}",
        flush=True
    )
    await ctx.send("Pong! 🏓")
# =========================================================
# SLASH PING
# =========================================================
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
# =========================================================
# CLEAR CHANNEL
# =========================================================
@bot.tree.command(
    name="clear",
    description="Delete all messages in this channel"
)
@discord.app_commands.checks.has_permissions(
    manage_messages=True
)
async def clear(interaction: discord.Interaction):
    print(
        "SLASH COMMAND RUNNING: /clear",
        flush=True
    )
    channel = interaction.channel
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.",
            ephemeral=True
        )
        return
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            "❌ This command can only be used in a text channel.",
            ephemeral=True
        )
        return
    bot_member = interaction.guild.me
    if bot_member is None:
        await interaction.response.send_message(
            "❌ I could not find my bot member in this server.",
            ephemeral=True
        )
        return
    permissions = channel.permissions_for(bot_member)
    print("========================================", flush=True)
    print("CLEAR COMMAND USED", flush=True)
    print(f"SERVER: {interaction.guild.name}", flush=True)
    print(f"CHANNEL: #{channel.name}", flush=True)
    print(f"USER: {interaction.user}", flush=True)
    print(f"BOT: {bot.user}", flush=True)
    print(
        f"VIEW CHANNEL: {permissions.view_channel}",
        flush=True
    )
    print(
        f"READ MESSAGE HISTORY: "
        f"{permissions.read_message_history}",
        flush=True
    )
    print(
        f"MANAGE MESSAGES: "
        f"{permissions.manage_messages}",
        flush=True
    )
    print("========================================", flush=True)
    if not permissions.view_channel:
        await interaction.response.send_message(
            "❌ The bot cannot View Channel.",
            ephemeral=True
        )
        return
    if not permissions.read_message_history:
        await interaction.response.send_message(
            "❌ The bot cannot Read Message History.",
            ephemeral=True
        )
        return
    if not permissions.manage_messages:
        await interaction.response.send_message(
            "❌ Discord says the bot does NOT have "
            "Manage Messages in this channel.\n\n"
            "The permission must be allowed for the "
            "BOT'S role in this channel.",
            ephemeral=True
        )
        return
    await interaction.response.defer(
        ephemeral=True
    )
    try:
        print(
            f"STARTING CLEAR IN #{channel.name}",
            flush=True
        )
        deleted_messages = await channel.purge(
            limit=None,
            bulk=True
        )
        deleted_count = len(deleted_messages)
        print(
            f"CLEAR COMPLETE: "
            f"{deleted_count} messages deleted",
            flush=True
        )
        await interaction.followup.send(
            f"🧹 **Channel cleared!**\n"
            f"Deleted **{deleted_count} messages**.",
            ephemeral=True
        )
    except discord.Forbidden as error:
        print(
            f"DISCORD FORBIDDEN ERROR: {error}",
            flush=True
        )
        await interaction.followup.send(
            "❌ Discord rejected the deletion.\n\n"
            "The bot's actual channel permissions "
            "do not allow the deletion.",
            ephemeral=True
        )
    except discord.HTTPException as error:
        print(
            f"DISCORD HTTP ERROR: {error}",
            flush=True
        )
        await interaction.followup.send(
            "❌ Discord returned an HTTP error "
            "while clearing the channel.",
            ephemeral=True
        )
    except Exception as error:
        print(
            f"CLEAR ERROR: {error}",
            flush=True
        )
        await interaction.followup.send(
            "❌ Something went wrong while clearing "
            "the channel. Check the Render logs.",
            ephemeral=True
        )
# =========================================================
# SNIPE SCANNER
# =========================================================
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
                "🔎 No matching coins found right now."
            )
            return
        message = (
            "**🎯 FOMO SNIPE SCANNER**\n\n"
        )
        for coin in coins:
            name = coin.get(
                "name",
                "Unknown"
            )
            symbol = coin.get(
                "symbol",
                "???"
            )
            chain = coin.get(
                "chain",
                "Unknown"
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
            age = coin.get(
                "age",
                "Unknown"
            )
            address = coin.get(
                "address",
                "Unknown"
            )
            url = coin.get("url")
            bubble_url = coin.get(
                "bubblemaps"
            )
            message += (
                f"🪙 **{name} ({symbol})**\n"
                f"⛓️ Chain: **{chain}**\n"
                f"💰 Market Cap: "
                f"**${market_cap:,.0f}**\n"
                f"💧 Liquidity: "
                f"**${liquidity:,.0f}**\n"
                f"📈 24h Volume: "
                f"**${volume:,.0f}**\n"
                f"🕐 Live for: **{age}**\n"
                f"📍 Contract: `{address}`\n"
            )
            if url:
                message += (
                    f"🔗 [Coin / Chart]({url})\n"
                )
            if bubble_url:
                message += (
                    f"🫧 [Bubblemaps]"
                    f"({bubble_url})\n"
                )
            message += "\n"
        if len(message) <= 2000:
            await interaction.followup.send(
                message
            )
        else:
            chunks = []
            current = ""
            for line in message.splitlines(
                keepends=True
            ):
                if len(current) + len(line) > 1900:
                    chunks.append(current)
                    current = line
                else:
                    current += line
            if current:
                chunks.append(current)
            for chunk in chunks:
                await interaction.followup.send(
                    chunk
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
# =========================================================
# GLOBAL COMMAND ERROR HANDLER
# =========================================================
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError
):
    print(
        "========================================",
        flush=True
    )
    print(
        "SLASH COMMAND ERROR",
        flush=True
    )
    print(
        f"ERROR TYPE: {type(error).__name__}",
        flush=True
    )
    print(
        f"ERROR: {error}",
        flush=True
    )
    print(
        "========================================",
        flush=True
    )
# =========================================================
# SLASH COMMAND SYNC
# =========================================================
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
# =========================================================
# START BOT
# =========================================================
print("========================================", flush=True)
print("STARTING DISCORD BOT...", flush=True)
print("========================================", flush=True)
bot.run(TOKEN)
