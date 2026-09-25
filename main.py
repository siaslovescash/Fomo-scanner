import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}! 👋")


@bot.command()
async def helpme(ctx):
    await ctx.send(
        "**🤖 FOMO Bot Commands**\n\n"
        "`!ping` - Check if the bot is working\n"
        "`!hello` - Say hello\n"
        "`!helpme` - Show this command list\n"
        "`!rules` - Show the server rules\n"
        "`!serverinfo` - Show server information\n"
        "`!userinfo` - Show your user information\n"
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
        description=f"Information about **{guild.name}**",
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
        description=f"Information about **{user}**",
    )

    embed.add_field(name="Username", value=str(user))
    embed.add_field(name="User ID", value=str(user.id))
    embed.add_field(
        name="Account Created",
        value=user.created_at.strftime("%Y-%m-%d"),
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


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need **Manage Messages** permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: `!clear <number>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please enter a valid number. Example: `!clear 10`")


bot.run(TOKEN)
