
import discord
from discord.ext import commands
import datetime
import re
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")


# Replace this with your #machine-maintenance channel ID
CHANNEL_ID = 1305654906639745044

# Configure bot intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True  # Needed to read messages

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.command()
async def unresolved(ctx):
    """Fetch and display unresolved maintenance issues from the last 90 days, grouped by machine name, and DM results."""
    
    # Notify the user that results are being sent via DM
    await ctx.send(f"📩 Check your DMs, {ctx.author.mention}!")

    try:
        # Open DMs with the user
        dm_channel = await ctx.author.create_dm()

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            await dm_channel.send("❌ Error: Channel not found.")
            return

        # Calculate cutoff date (90 days ago) with timezone-aware datetime
        days_to_go_back = 90  # ⬅️ Increased from 60 to 90 days
        now = datetime.datetime.now(datetime.UTC)
        cutoff_date = now - datetime.timedelta(days=days_to_go_back)

        # Fetch messages after the cutoff date
        messages = [message async for message in channel.history(after=cutoff_date)]

        # Dictionary to store unresolved issues grouped by machine
        unresolved_issues = {}

        # Adjusted regex pattern to match the correct message format
        report_pattern = re.compile(
            r"🚨 \*\*New Maintenance Report\*\* 🚨\s*"
            r"👤 \*\*Submitted by:\*\* (.+)\s*"
            r"🛠 \*\*Machine:\*\* (.+)\s*"
            r"⚠ \*\*Issue:\*\* (.+)",
            re.DOTALL
        )

        for message in messages:
            if any(reaction.emoji == "✅" for reaction in message.reactions):
                continue  # Skip if marked resolved

            match = report_pattern.search(message.content)
            if match:
                _, machine, issue = match.groups()  # Ignore the submitter's name
                if machine not in unresolved_issues:
                    unresolved_issues[machine] = []
                unresolved_issues[machine].append(f"   • {issue}")  # ⬅️ Bullet point format

        # Format output (Compact, Readable)
        if unresolved_issues:
            response = "**🚨 Unresolved Maintenance Issues (Last 90 Days):**\n"
            for machine, issues in unresolved_issues.items():
                response += f"\n🕹 **{machine}**\n" + "\n".join(issues) + "\n"

            # Split long messages into chunks (Discord limit: 2000 characters)
            MAX_MESSAGE_LENGTH = 2000
            messages_to_send = []
            while len(response) > 0:
                if len(response) > MAX_MESSAGE_LENGTH:
                    split_index = response.rfind("\n🕹", 0, MAX_MESSAGE_LENGTH)
                    if split_index == -1:  # Fallback in case no good split point is found
                        split_index = MAX_MESSAGE_LENGTH

                    messages_to_send.append(response[:split_index])
                    response = response[split_index:]
                else:
                    messages_to_send.append(response)
                    break

            for msg in messages_to_send:
                await dm_channel.send(msg)  # Send the messages via DM

        else:
            await dm_channel.send("✅ All maintenance issues from the last 90 days are resolved!")

    except discord.errors.Forbidden:
        await ctx.send("❌ I couldn't DM you! Please enable DMs from server members.")

bot.run(TOKEN)
