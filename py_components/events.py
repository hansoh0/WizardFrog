"""
Bot lifecycle and gateway event listeners:

on_ready():
Starts the announce_events, change_bot_status, and check_sites background
tasks, then runs the member join backfill once on startup

on_error():
Catches any event handler exception and prints the traceback

on_member_join():
Sends the welcome message, assigns the "user" role, and records the
new member in userlist.txt

on_voice_state_update():
Stops playback and disconnects bot if the voice channel it's in becomes empty

_get_members():
Compares the server's member list against userlist.txt and sends a
catch-up welcome message for anyone missed while the bot was offline
"""

import os
import traceback

import discord

import announcements
import site_monitor
from bot_instance import bot
from config import SERVID, WELCID, WPATH
from music import queue


@bot.event
async def on_ready():
    """
    Bot Startup Events
    -> Runs announce events method from announceEventsController
    -> Runs member retrival method from memberWatchController
    -> Prints status
    """
    announcements.announce_events.start()
    await _get_members()
    print("GoodMorning")
    announcements.change_bot_status.start()
    site_monitor.check_sites.start()


@bot.event
async def on_error(event, *args, **kwargs):
    """
    Bot Catch Errors
    -> Catches event name and subsequent error
    -> Prints the traceback
    """
    error_message = traceback.format_exc()
    print(f"Error in {event}: {error_message}")


@bot.event
async def on_member_join(ctx):
    """
    Member Join Listener
    -> Listens for member joing and sends welcome message
    -> Adds role "user" to new members
    -> Adds user to known users list
    """
    channel = bot.get_channel(WELCID)
    await channel.send(f'{ctx.mention}')
    role = discord.utils.get(ctx.guild.roles, name='user')
    await ctx.add_roles(role)
    with open(str(WPATH + '/LOGS/userlist.txt'), 'a') as userlist:
        user_id = ctx.id
        userlist.write(str(user_id) + '\n')


@bot.event
async def on_voice_state_update(ctx, before, after):
    """
    VC Status Listener
    -> If VC is empty, stop music, cleanup, and leave
    """
    try:
        if ctx.guild.voice_client and len(ctx.guild.voice_client.channel.members) == 1:
            ctx.guild.voice_client.stop()
            for item in queue:
                filename = item.split(';')[0]
                os.remove(filename)
            queue.clear()
            await ctx.guild.voice_client.disconnect()
    except:
        print("Not able to disconnect.")


async def _get_members():
    """
    Member Join Offline Compensator
    -> Checks if all users in server have been accounted for
    -> Depending on # of missed users, either joint welcome or single
    -> Saves new users to member list
    """
    # TODO: This will need a better sorting algorithm and is literally frankensteins monster
    planets = ['Zeffo', 'Tatooine', 'Endor', 'Kamino', 'Jakku', 'Kashyyyk', 'Alderaan', 'Mustafar', 'Tinnel IV', 'Saki', 'Rion', 'Ojom', 'Naboo', 'Naraka', 'Ando', 'Affadar', 'Aargonar']
    guild_id = SERVID
    guild = bot.get_guild(guild_id)
    channel = bot.get_channel(WELCID)
    file_path = WPATH + '/LOGS/userlist.txt'
    users_to_add = {}
    try:
        # Read user list, if file doesnt exist, make it
        users = []
        try:
            with open(file_path, 'r') as user_file:
                users = user_file.readlines()
        except FileNotFoundError:
            with open(file_path, 'w') as user_file:
                pass
        # Iterate through server members
        for user in guild.members:
            user_id = user.id
            # If user isnt in our userlist, add them to dict
            if str(user_id) + '\n' not in users:
                users_to_add[str(user)] = (user_id)
        # If there are new members
        if len(users_to_add) >= 1:
            # If theres only one new member
            if len(users_to_add) == 1:
                member = guild.get_member_named(next(iter(users_to_add)))
                # SENDING WELCOME TO SINGLE
                await channel.send(f"Hello there {member.mention}, welcome to the club!")
            else:
                cnt = 1
                message = "Hello there "
                for user, user_id in users_to_add.items():
                    if cnt == len(users_to_add):
                        message = message + f'and {guild.get_member_named(user).mention}!'
                    # Handles only two new people
                    elif len(users_to_add) == 2:
                        message = message + f'{guild.get_member_named(user).mention} '
                    else:
                        message = message + f'{guild.get_member_named(user).mention}, '
                    cnt += 1
                message = message + "! Welcome to the club!"
                # SENDING WELCOME TO MULTIPLE
                await channel.send(f'{message}')

            # Modify the saved user list
            with open(file_path, 'a') as user_file:
                for user, user_id in users_to_add.items():
                    user_file.write(str(user_id) + '\n')
    except Exception as e:
        print(f'Error in _get_members: {e}')
