"""
Misc / fun commands, and the help page:

show_help():
!help - Prints the full command list grouped by category

hackers():
!hackers - Sends a Hackers (1995) movie quote

troll_detected():
!trolldetected - Sends the "troll detected" bit

beep():
!beep - Replies "boop"

thanks():
!thanks - Sends a random line from R2
"""

import random
import time as t

from bot_instance import bot
from config import quips


@bot.command(name='help', help='Displays help page')
async def show_help(ctx):
    """
    Bot Display Commands
    -> Displays the different commands a user can use
    """
    text = (
        "**Misc Commands**```\n\n"
        "!help\n- Shows this message\n\n"
        "!mcstatus\n- Gets the status of the minecraft server\n\n"
        "!suggest \"[suggestion]\"\n- Make a /suggestion\n\n"
        "!thanks\n- Give thanks to the wizard frog\n\n"
        "!random [gif, pic, fact, movie, song]\n- Recieve a random gif, pic, fact, movie, or song\n\n"
        "!submit [gif, pic, fact, movie, song] [link, text, pic, gif]\n- Submit an image, fact, movie, or song to add to the !random command\n\n"
        "```**Role Commands**```\n\n"
        "!roles\n- Lists all roles on the server\n\n"
        "!role \"[role]\"\n- Assigns specified role to the user\n\n"
        "!rmrole \"[role]\"\n- Removes specified role from user\n\n"
        "!sub\n- Subscribes user to announcements\n\n"
        "!unsub\n- Unsubscribes user from getting announcements\n\n"
        "```**Jukebox Commands**```\n\n"
        "!join\n- Make bot Jukebox join your voice channel\n\n"
        "!leave\n- Instruct bot to leave the current voice channel\n\n"
        "!q [youtube link]\n- Submit a song to the jukebox queue\n\n"
        "!lsq\n- View the current song queue\n\n"
        "!start\n- Start the jukebox\n\n"
        "!stop\n- Stop the jukebox\n\n"

        "```\n"
        "*Not all random categories are currently available*\n*Please make sure to use quotes where necessary!*\n"
    )
    await ctx.send(text)


@bot.command(name='hackers', help='Mess with me')
async def hackers(ctx):
    """
    Bot Hacker Quote
    -> Mess with the best...
    """
    await ctx.send('Incoming Transmission from Zero Cool:')
    t.sleep(2)
    await ctx.send('Mess with the best...')
    t.sleep(0.5)
    await ctx.send('Die like the rest.')
    t.sleep(0.5)
    await ctx.send('Hack the planet!')


@bot.command(name='trolldetected', help='blastem!')
async def troll_detected(ctx):
    """
    Bot Troll Detected
    -> Roger Roger
    """
    await ctx.send('🚨 TROLL DETECTED 🚨')
    t.sleep(1)
    await ctx.send('💥 BLAST \'EM 💥')


@bot.command(name='beep', help='beep boop')
async def beep(ctx):
    """
    Bot Ping
    -> Ping, Pong
    """
    await ctx.send('boop')


@bot.command(name='thanks', help='give thanks')
async def thanks(ctx):
    """
    Bot Thanks
    -> +1 Charisma
    """
    await ctx.send(random.choice(quips))