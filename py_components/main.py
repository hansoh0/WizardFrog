#! /usr/bin/env python3
"""
Entry point.

imports config and bot_instance for TOKEN/bot, 
imports every feature module so their commands/events register
on bot as a side effect, then calls bot.run(TOKEN) and cleans up
leftover jukebox files on exit.
"""


from bot_instance import bot
from config import TOKEN

# Importing these registers their commands/events on bot as a side effect.
import music
import roles
import announcements
import submissions
import fun
import events
import minecraft
import site_monitor

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Something went wrong when initializing the bot: {e}")
    finally:
        music.cleanup_end()
