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
    print(f"WEB SERVER STARTED ON PORT {port}")
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
# BOT READY
# =========================================================
@bot.event
async def on_ready():
    print("========================================")
    print("BOT IS ONLINE")
    print(f"BOT NAME: {bot.user}")
    print(f"BOT ID: {bot.user.id}")
    print(f"SERVERS: {len(bot.guilds)}")
    for guild in bot.guilds:
        print(
            f"SERVER: {guild.name} | "
            f"ID: {guild.id}"
        )
    print("========================================")
# =========================================================
# PREFIX PING
# =========================================================
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")
# =========================================================
# SLASH PING
# =========================================================
@bot.tree.command(
    name="ping",
    description="Check if the bot is online"
)
async def slash_ping(
    interaction: discord.Interaction
):
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
async def clear(
    interaction: discord.Interaction
):
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
    # Get the bot's member object in this server
    bot_member = interaction.guild.me
    if bot_member is None:
        await interaction.response.send_message(
            "❌ I could not find my bot member in this server.",
            ephemeral=True
        )
        return
    # Check the bot's REAL permissions in this channel
    permissions = channel.permissions_for(bot_member)
    print("========================================")
    print("CLEAR COMMAND USED")
    print(f"SERVER: {interaction.guild.name}")
    print(f"CHANNEL: #{channel.name}")
    print(f"USER: {interaction.user}")
    print(f"BOT: {bot.user}")
    print(
        f"VIEW CHANNEL: "
        f"{permissions.view_channel}"
    )
    print(
        f"READ MESSAGE HISTORY: "
        f"{permissions.read_message_history}"
    )
    print(
        f"MANAGE MESSAGES: "
        f"{permissions.manage_messages}"
    )
    print("========================================")
    # Check View Channel
    if not permissions.view_channel:
        await interaction.response.send_message(
            "❌ The bot cannot View Channel.",
            ephemeral=True
        )
        return
    # Check Read Message History
    if not permissions.read_message_history:
        await interaction.response.send_message(
            "❌ The bot cannot Read Message History.",
            ephemeral=True
        )
        return
    # Check Manage Messages
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
            f"STARTING CLEAR IN #{channel.name}"
        )
        # Delete messages from the channel.
        #
        # discord.py handles newer messages with
        # Discord's bulk-delete system and older
        # messages individually.
        deleted_messages = await channel.purge(
            limit=None,
            bulk=True
        )
        deleted_count = len(
            deleted_messages
        )
        print(
            f"CLEAR COMPLETE: "
            f"{deleted_count} messages deleted"
        )
        await interaction.followup.send(
            f"🧹 **Channel cleared!**\n"
            f"Deleted **{deleted_count} messages**.",
            ephemeral=True
        )
    except discord.Forbidden as error:
        print(
            f"DISCORD FORBIDDEN ERROR: {error}"
        )
        await interaction.followup.send(
            "❌ Discord rejected the deletion.\n\n"
            "The bot's actual channel permissions "
            "do not allow the deletion.",
            ephemeral=True
        )
    except discord.HTTPException as error:
        print(
            f"DISCORD HTTP ERROR: {error}"
        )
        await interaction.followup.send(
            "❌ Discord returned an HTTP error "
            "while clearing the channel.",
            ephemeral=True
        )
    except Exception as error:
        print(
            f"CLEAR ERROR: {error}"
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
async def snipe(
    interaction: discord.Interaction
):
    await interaction.response.defer()
    try:
        coins = await snipe_scan()
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
        # Discord has a 2,000 character
        # message limit.
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
            f"SNIPE ERROR: {error}"
        )
        await interaction.followup.send(
            "❌ The scanner encountered an error. "
            "Check the Render logs."
        )
# =========================================================
# SLASH COMMAND SYNC
# =========================================================
@bot.event
async def setup_hook():
    print("========================================")
    print("SYNCING SLASH COMMANDS...")
    print("========================================")
    try:
        synced = await bot.tree.sync()
        print(
            f"SYNCED {len(synced)} SLASH COMMAND(S)"
        )
        for command in synced:
            print(
                f"REGISTERED: /{command.name}"
            )
    except Exception as error:
        print(
            f"SLASH COMMAND SYNC ERROR: {error}"
        )
# =========================================================
# START BOT
# =========================================================
print("========================================")
print("STARTING DISCORD BOT...")
print("========================================")
bot.run(TOKEN)
