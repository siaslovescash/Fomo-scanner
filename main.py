import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "coins.db"


def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER NOT NULL DEFAULT 0,
            last_daily TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT coins, last_daily FROM users WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    if result is None:
        cursor.execute(
            "INSERT INTO users (user_id, coins) VALUES (?, 0)",
            (user_id,)
        )
        conn.commit()
        result = (0, None)
    conn.close()
    return result


def set_coins(user_id, amount):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO users (user_id, coins) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET coins = ?",
        (user_id, amount, amount)
    )
    conn.commit()
    conn.close()


setup_database()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as error:
        print(f"Slash command sync error: {error}")


# -------------------------
# PREFIX COMMANDS
# -------------------------

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}! 👋")


@bot.command()
async def balance(ctx):
    coins, _ = get_user(ctx.author.id)
    await ctx.send(
        f"🪙 {ctx.author.mention}, you have **{coins:,} coins**!"
    )


@bot.command()
async def daily(ctx):
    from datetime import date

    user_id = ctx.author.id
    coins, last_daily = get_user(user_id)
    today = str(date.today())

    if last_daily == today:
        await ctx.send(
            f"⏰ {ctx.author.mention}, you already claimed your daily coins!"
        )
        return

    coins += 100
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "UPDATE users SET coins = ?, last_daily = ? WHERE user_id = ?",
        (coins, today, user_id)
    )
    conn.commit()
    conn.close()

    await ctx.send(
        f"🎁 {ctx.author.mention} received **100 coins**!\n"
        f"💰 Balance: **{coins:,} coins**"
    )


@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Enter an amount greater than 0.")
        return

    sender_coins, _ = get_user(ctx.author.id)
    if sender_coins < amount:
        await ctx.send("❌ You don't have enough coins.")
        return

    receiver_coins, _ = get_user(member.id)
    set_coins(ctx.author.id, sender_coins - amount)
    set_coins(member.id, receiver_coins + amount)

    await ctx.send(
        f"💸 {ctx.author.mention} gave **{amount:,} coins** "
        f"to {member.mention}!"
    )


@bot.command()
async def leaderboard(ctx):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10"
    )
    users = cursor.fetchall()
    conn.close()

    if not users:
        await ctx.send("🏆 Nobody has any coins yet!")
        return

    text = "**🏆 FOMO Coin Leaderboard**\n\n"
    for position, (user_id, coins) in enumerate(users, start=1):
        user = bot.get_user(user_id)
        name = user.mention if user else f"User {user_id}"
        text += f"**{position}.** {name} — 🪙 **{coins:,}**\n"

    await ctx.send(text)


@bot.command()
async def helpme(ctx):
    await ctx.send(
        "**🤖 FOMO Bot Commands**\n\n"
        "**🪙 Coins**\n"
        "`!balance` - Check your coins\n"
        "`!daily` - Claim 100 daily coins\n"
        "`!give @user amount` - Give coins\n"
        "`!leaderboard` - Coin leaderboard\n\n"
        "**🔧 General**\n"
        "`!ping` - Check the bot\n"
        "`!hello` - Say hello\n"
        "`!rules` - Server rules\n"
        "`!serverinfo` - Server information\n"
        "`!userinfo` - User information\n"
        "`!clear <number>` - Delete messages\n"
        "`!say <message>` - Make the bot say something"
    )


@bot.command()
async def rules(ctx):
    await ctx.send(
        "**📜 Server Rules**\n\n"
        "1. Be respectful.\n"
        "2. No spam.\n"
        "3. No harassment.\n"
        "4. Follow Discord's Terms and Community Guidelines.\n"
        "5. Have fun! 🎉"
    )


@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild

    embed = discord.Embed(
        title="📊 Server Information",
        description=f"Information about **{guild.name}**"
    )
    embed.add_field(name="Members", value=str(guild.member_count))
    embed.add_field(name="Channels", value=str(len(guild.channels)))
    embed.add_field(name="Server ID", value=str(guild.id))
    embed.add_field(name="Owner", value=str(guild.owner))

    await ctx.send(embed=embed)


@bot.command()
async def userinfo(ctx):
    user = ctx.author

    embed = discord.Embed(
        title="👤 User Information",
        description=f"Information about **{user}**"
    )
    embed.add_field(name="Username", value=str(user))
    embed.add_field(name="User ID", value=str(user.id))
    embed.add_field(
        name="Account Created",
        value=user.created_at.strftime("%Y-%m-%d")
    )

    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount < 1:
        await ctx.send("Please choose a number greater than 0.")
        return

    if amount > 100:
        await ctx.send("You can only delete up to 100 messages at once.")
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    message = await ctx.send(
        f"🧹 Deleted {len(deleted) - 1} message(s)."
    )
    await message.delete(delay=5)


@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)


# -------------------------
# SLASH COMMANDS
# -------------------------

@bot.tree.command(name="balance", description="Check your FOMO coins")
async def slash_balance(interaction: discord.Interaction):
    coins, _ = get_user(interaction.user.id)
    await interaction.response.send_message(
        f"🪙 {interaction.user.mention}, you have **{coins:,} coins**!"
    )


@bot.tree.command(name="daily", description="Claim your daily 100 coins")
async def slash_daily(interaction: discord.Interaction):
    from datetime import date

    user_id = interaction.user.id
    coins, last_daily = get_user(user_id)
    today = str(date.today())

    if last_daily == today:
        await interaction.response.send_message(
            "⏰ You already claimed your daily coins!"
        )
        return

    coins += 100
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "UPDATE users SET coins = ?, last_daily = ? WHERE user_id = ?",
        (coins, today, user_id)
    )
    conn.commit()
    conn.close()

    await interaction.response.send_message(
        f"🎁 You received **100 coins**!\n"
        f"💰 Balance: **{coins:,} coins**"
    )


@bot.tree.command(name="leaderboard", description="View the FOMO coin leaderboard")
async def slash_leaderboard(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10"
    )
    users = cursor.fetchall()
    conn.close()

    if not users:
        await interaction.response.send_message(
            "🏆 Nobody has any coins yet!"
        )
        return

    text = "**🏆 FOMO Coin Leaderboard**\n\n"
    for position, (user_id, coins) in enumerate(users, start=1):
        user = bot.get_user(user_id)
        name = user.mention if user else f"User {user_id}"
        text += f"**{position}.** {name} — 🪙 **{coins:,}**\n"

    await interaction.response.send_message(text)


@bot.tree.command(name="hello", description="Say hello to the bot")
async def slash_hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello, {interaction.user.mention}! 👋"
    )


@bot.tree.command(name="ping", description="Check if the bot is online")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")


@bot.tree.command(name="rules", description="Show the server rules")
async def slash_rules(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**📜 Server Rules**\n\n"
        "1. Be respectful.\n"
        "2. No spam.\n"
        "3. No harassment.\n"
        "4. Follow Discord's Terms and Community Guidelines.\n"
        "5. Have fun! 🎉"
    )


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You need **Manage Messages** permission to use this command."
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!clear <number>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(
            "Please enter a valid number. Example: `!clear 10`"
        )


bot.run(TOKEN)
