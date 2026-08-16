"""
Shared bot instance. Feature modules import bot from here to register
their commands and event listeners.

intents:
discord.Intents with everything enabled, passed into the bot

stop_event:
Unused asyncio.Event carried over from the original single file bot

bot:
The shared commands.Bot instance every other module registers against
"""

import asyncio
import discord
from discord.ext import commands

intents = discord.Intents().all()
stop_event = asyncio.Event()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
