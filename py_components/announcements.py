"""
Server announcements posted in ANNOID channel:

announce():
!announce - Manual announcements only allowed by those with role "Council" from CATHID channel

_update_events():
Updates all events from server events to stored events file schevents.txt

_retrieve_events():
Reads all events in schevents.txt

_write_event():
Writes new events from server events to schevents.txt

_remove_event():
Removes events in schevents.txt that does not correspond to a server event

_update_event():
Updates events in schevents.txt based on how long until the event is 

announce_events():
Announces any upcoming events with corresponding details and time frame.

_convert_time():
Helper to convert current time to programmable format

_get_time_span_choice():
Helper for updating events
"""

import random
import re
from datetime import datetime

import discord
import pytz
from discord.ext import tasks

from bot_instance import bot
from config import ANNOID, CATHID, SERVID, WPATH


@bot.command(name='announce', help='creates an announcement through r2')
async def announce(ctx, *, announcement: str):
    """
    Bot Create Announcement Command
    -> Allows users in a specified channel with specified role to make announcements
    -> If contains bad char, let em know
    -> Errors are printed
    """
    try:
        if ctx.channel.id != CATHID:
            print("Not actuated from the mod channel.")
            return
        role = discord.utils.get(ctx.guild.roles, name='Council')
        if role not in ctx.author.roles:
            return
        else:
            allowed_characters_pattern = r'[\w\s.!?,:;\'"“”&=/%-]+'
            if not re.match(allowed_characters_pattern, announcement):
                await ctx.send('Your announcement contains an illegal character, please review it and try again.')
                return
            # This announcement should only be made in a specified channel
            channel = bot.get_channel(ANNOID)
            ann_role = discord.utils.get(ctx.guild.roles, name='Announcements')
            await channel.send(f'{ann_role.mention} {announcement}')
    except Exception as e:
        print(f'ERROR announce: {e}')


async def _update_events():
    """
    Scheduled Event Sync
    -> Fetches all of the server's scheduled events
    -> Writes any new events to schevents.txt
    -> Removes any stored events that no longer exist on the server
    """
    guild_id = SERVID
    try:
        stored_events = await _retrieve_events()
        guild = bot.get_guild(guild_id)
        if guild:
            # Getting all scheduled events in Server
            events = await guild.fetch_scheduled_events()
            form_events = []
            if events:
                for event in events:
                    formatted_time = datetime.fromisoformat(str(event.start_time).replace('Z', '+00:00')).replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('America/New_York')).strftime("%m/%d %H:%M")
                    # Starting to format those events at: MM/DD HH:MM
                    schevent = f'{event.name};;{formatted_time}'
                    form_events.append(schevent)
                    # Taking the events in events txt file and removing bools.
                    stored_events_clean = [stored.replace(';;false', '').replace(';;true', '') for stored in stored_events]
                    if schevent not in stored_events_clean:
                        # Writing "Name;;MM/DD HH:MM;;weekBool;;dayOfBool;;threeDayBool"
                        print(f'Writing: {schevent}')
                        await _write_event(f'{event.name};;{formatted_time};;false;;false;;false')
                        continue
                    else:
                        pass

            for stored_event in stored_events:
                if stored_event.replace(';;false', '').replace(';;true', '') not in form_events:
                    print(f'Removing: {stored_event}')
                    await _remove_event(stored_event)
                else:
                    pass
        else:
            print(f'No guild found')
    except Exception as e:
        print(f'ERROR _update_events: {e}')


async def _retrieve_events():
    """
    Stored Event Reader
    -> Reads and returns every line from schevents.txt
    """
    scheduled_events = []
    try:
        with open((WPATH + '/schevents.txt'), 'r') as schevents:
            for event in schevents:
                scheduled_events.append(event.strip())
    except Exception as e:
        print(f'ERROR retrieve_event: {e}')
    finally:
        return scheduled_events


async def _write_event(event):
    """
    Stored Event Writer
    -> Appends a new event line to schevents.txt
    """
    try:
        with open((WPATH + '/schevents.txt'), 'a') as schevents:
            schevents.write(event + '\n')
    except Exception as e:
        print(f'ERROR _write_event: {e}')


async def _remove_event(event):
    """
    Stored Event Remover
    -> Removes a specific event line from schevents.txt
    """
    try:
        with open((WPATH + '/schevents.txt'), 'r') as schevents:
            scheduled_events = schevents.readlines()

        with open((WPATH + '/schevents.txt'), 'w') as schevents:
            for schevent in scheduled_events:
                if schevent.strip() != event:
                    schevents.write(schevent)
    except Exception as e:
        print(f'ERROR _remove_event: {e}')


async def _update_event(event, mode):
    """
    Stored Event Updater
    -> Removes and re-writes an event line with its week/day/three-day reminder flag set
    """
    try:
        await _remove_event(event)
        split_event = event.split(";;")
        # Mode selected is one week
        if mode == '1':
            await _write_event(f'{split_event[0]};;{split_event[1]};;true;;{split_event[3]};;{split_event[4]}')
        # Mode selected is one day
        elif mode == '2':
            await _write_event(f'{split_event[0]};;{split_event[1]};;{split_event[2]};;true;;{split_event[4]}')
        # Mode selected is three day
        elif mode == '3':
            await _write_event(f'{split_event[0]};;{split_event[1]};;{split_event[2]};;{split_event[3]};;true')
    except Exception as e:
        print(f'ERROR _update_event: {e}')


#################################################
# TASKS +++++++++++++++++++++++++++++++++++++++++
#################################################

@tasks.loop(seconds=3600)
async def announce_events():
    """
    Hourly Event Announcer
    -> Only runs during the 11am hour
    -> Syncs stored events, then announces any that are one week, three days, or one day out
    """
    ## Should only execute if it is 11am-11:59am
    if str(datetime.now().hour) == '11':
        print('Running announcements')
        try:
            stored_events = await _retrieve_events()
            await _update_events()
            current_date = datetime.now()

            for event in stored_events:
                # Log
                print(f'Testing: {event}')

                date = event.split(';;')[1].split(' ')[0]

                # Month of event matches
                if date.split('/')[0] == str("{:02d}".format(current_date.month)):

                    # Getting a few variables.
                    channel = bot.get_channel(ANNOID)
                    role = discord.utils.get(bot.get_guild(SERVID).roles, name='announcements')
                    d = date.split('/')[1]
                    n = event.split(';;')[0]
                    t = event.split(';;')[1].split(' ')[1]
                    time_span = ['in one week', 'in three days', 'tomorrow']  # Need to update how events are stored
                    LP_link = 'https://www.eventbrite.com/e/lockpicking-learners-group-tickets-707450733187'

                    # Log
                    print(f'Retrieved Role: {role} Day: {d} Event: {n}')

                    # Crafing Announcmement to be made, if any
                    msg = await _craft_announcement(role, n, t, d, time_span, LP_link, current_date, event)

                    # Sending annnouncement to announcmeent channel
                    if msg != None:
                        await channel.send(msg)

        except Exception as e:
            print(f'ERROR announce_events: {e}')


@tasks.loop(seconds=5400)
async def change_bot_status():
    """
    Bot Status Rotator
    -> Picks a random song, movie, game, or custom activity and sets it as bots presence
    """
    print('Executing Status Change')
    sample_songs = ['God\'s Plan - Drake',
    'All the Things - Dual Core',
    'Casting Spells - Danger Incorporated',
    'Chippin\' in - SAMURAI',
    'Bitcoin Baron - YTCracker',
    'DMG We Trust in Thee - Supercommuter',
    'Spaz - N.E.R.D',
    'Imprisoned by the Syndicate - YTCracker',
    'Can\'t Sleep - K.flay',
    'On Melancholy Hill - Gorillaz',
    'I Really Want to Stay at Your Hose - Rosa Walton',
    'No Save Point - Run The Jewels',
    'Void (No Return) - Dual Core',
    'Fear & Chaos - Dual Core',
    'Cipher Punks - Dual Core',
    'SMTP - Yung Innanet',
    'Clickin\' - Ohm-I',
    'Them THANGS - Ohm-I',
    'Bugabuse - ELIOZE',
    'Who\'s Ready for Tomorrow - RAT BOY',
    'Friday Night Fire Fight - Aligns']

    sample_movies = ['Star Wars: Episode I - The Phantom Menace',
    'Star Wars: Episode II - Attack of the Clones'
    'Star Wars: Episode III - Revenge of the Sith',
    'Star Wars: Episode IV - A New Hope',
    'Star Wars: Episode V - The Empire Strikes Back',
    'Star Wars: Episode VI - Return of the Jedi',
    'Star Wars: Episode VII - The Force Awakens',
    'Star Wars: Episode VIII - The Last Jedi',
    'Star Wars: Episode IX - The Rise of Skywalker',
    'Rogue One: A Star Wars Story',
    'Solo: A Star Wars Story',
    'Ghost in the Shell',
    'Blade Runner',
    'Blade Runner 2049',
    'The Matrix',
    'Tron',
    'Akira']

    sample_games = ['Hack the Box',
    'TryHackMe',
    'BitBurner',
    'Cyberpunk: 2077',
    'Star Wars: Battlefront',
    'Deus Ex',
    'System Shock 2',
    'Ruiner',
    'Syndicate',
    'with 1s and 0s']

    sample_actions = [ 'Dilly Dallying',
    'Fooling with Tom',
    'Taking the Piss',
    'Locked in',
    'Wiz Biz']

    sample_emojis = [ '🥸',
    '🤪',
    '🥴',
    '🫦',
    '🕵️',
    '🧙‍♂️',
    '⚠️',
    '🚭']

    activities = [discord.Activity(type=discord.ActivityType.listening, name=random.choice(sample_songs)),
    discord.Activity(type=discord.ActivityType.watching, name=random.choice(sample_movies)),
    discord.Game(name=random.choice(sample_games)),
    discord.CustomActivity(name=random.choice(sample_actions), emoji=random.choice(sample_emojis))]

    await bot.change_presence(activity=random.choice(activities))


async def _craft_announcement(role, n, t, d, time_span, LP_link, current_date, event):
    """
    Announcement Text Builder
    -> Determines the correct time-span wording for an event
    -> Builds the announcement message from the matching template (LP/DC614/test/default)
    -> Returns None if there's nothing to announce yet
    """
    ann_to_send = None

    # Grabbing the right time span choice
    time_span_choice = await _get_time_span_choice(time_span, d, current_date, n, event)

    # Converting time
    t = await _convert_time(t)

    DC_location = 'The Daily Growler'

    DC_templates = [f'']

    LP_templates = [f'']

    if time_span_choice != None:
        # Lockpicking learners group
        if "lockpicking" in n.lower() and "learners" in n.lower():
            ann_to_send = random.choice(LP_templates)

        # Dc614
        elif "614" in n.lower():
            ann_to_send = random.choice(DC_templates)

        # Test announcement
        elif "test" in n.lower():
            try:
                random.choice(LP_templates)
                random.choice(DC_templates)
            except Exception as e:
                print('Something went wrong when attempting to grab an announcment. See _craft_announcement.')

            ann_to_send = 'Testing Announcement System... Please Stand By...'

        else:
            ann_to_send = f'{role.mention} {n} is coming up **{time_span_choice}**! Be sure to check out the details in the events tab if you\'re interested!'

    return ann_to_send


async def _convert_time(time):
    """
    Time Converter
    -> Converts Military time to standard
    """
    try:
        mil_time = datetime.strptime(time, "%H:%M")
        std_time = mil_time.strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return '12:00 AM'
    except Exception as e:
        print(f'Error in _convert_time: {e}')
    return std_time


async def _get_time_span_choice(time_span, day, current_date, n, event):
    """
    Reminder Window Checker
    -> Checks if today is one week, three days, or one day before the event
    -> Marks the corresponding reminder flag as sent and returns the matching time-span text
    -> Also acts as the check for whether an announcement should be made at all
    """
    # This function also acts as a check if theres even an announcment to be given

    time_span_choice = None

    # If today is one week before
    if str((int(day) - 8)) == str(current_date.day):
        # LOG
        print(f'Event {n} is one week before')
        if event.split(';;')[3] != 'true':
            time_span_choice = time_span[0]
            await _update_event(event, '1')

    # If today is one before
    elif str(int(day) - 1) == str(current_date.day):
        # LOG
        print(f'Event {n} is tommorow')
        if event.split(';;')[3] != 'true':
            time_span_choice = time_span[2]
            await _update_event(event, '2')

    # If today is three before
    elif str(int(day) - 3) == str(current_date.day):
        # LOG
        print(f'Event {n} is 3 days before')
        if event.split(';;')[3] != 'true':
            time_span_choice = time_span[1]
            await _update_event(event, '3')

    return time_span_choice
