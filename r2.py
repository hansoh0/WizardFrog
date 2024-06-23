#! /usr/bin/env python3

import random, re, os, discord, asyncio, pytz, sys
from systemd import journal
from discord.ext import commands,tasks
from dotenv import load_dotenv
from datetime import datetime,time
import yt_dlp as youtube_dl
import time as t

load_dotenv() 

# ENV Globals
TOKEN = os.getenv("TOKEN")
SERVID = int(os.getenv("SERVID"))
WELCID = int(os.getenv("WELCID"))
ANNOID = int(os.getenv("ANNOID"))
CATHID = int(os.getenv("CATHID"))
WPATH = os.getenv("ROOT")

# Bot Globals
R2 = ["Bleep bloop blop beep!","Beep beep boop beep","Beep bloop beep!", "Beep beep boop!", 
"Bleep boop beep beep!", "Beep beep bloop!", "Beep boop!", "Beep beep bloop beep!", 
"Beep beep boop bloop!", "Beep boop bloop!", "Beep beep bloop beep boop!", "Beep beep boop blop!", 
"Beep boop beep bloop beep!", "Beep beep boop bloop beep blop!", "Beep beep boop bloop beep boop!" ]
voice_controller = None
intents = discord.Intents().all()
#client = discord.Client(intents=intents)
stop_event = asyncio.Event()
bot = commands.Bot(command_prefix='!',intents=intents,help_command=None)
restricted_roles = ["chaos_machine","NCL","PicoCTF","ChaosComputerClub","Starboard", "warden","bot herder", "=== cosmetic ===", "=== bots ===", "=== functional ===", "R2", "
announcements"]

# Music Globals
queue = []
playing_filenames = {}
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
    'outtmpl': WPATH+'/JUKE/%(title)s.%(ext)s'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

'''
YT Download Class
'''
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""
        self.track_length = data.get('duration', 0)

    '''
    Download From YT URL
    -> Removes events from event db
    -> Returns file, title, duration of downloaded content
    '''
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename, data.get('title'), str(data.get('duration', 0))

'''
Download Cleanup Catch Class
'''
class FileCleanup:
    def __init__(self, filename):
        self.filename = filename

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            os.remove(self.filename)
        except Exception as e:
            journal.send(f"Error deleting file: {e}")

'''
File remover
-> Removes all files .webm in JUKE directory in file root
'''
def cleanup_end():
    for item in os.listdir(WPATH+"/JUKE"):
        if item.endswith(".webm"):
            os.remove(WPATH+"/JUKE/"+item)

'''
Bot Join VC Command
-> Makes Bot join callers VC
-> If caller not in VC, let em know
-> If Bot in another VC, let em know
'''
@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    global voice_controller
    if ctx.guild.voice_client is not None:
        await ctx.send(f'Sorry, im already hanging out in {ctx.guild.voice_client.channel.mention}.')
        return
    if not ctx.message.author.voice:
        await ctx.send(f'Sorry {ctx.message.author.name}, you don\'t look to be connected to a voice channel')
        return
    else:
        channel = ctx.message.author.voice.channel
    voice_controller = ctx.author.name
    await channel.connect()

'''
Bot Leave VC Command
-> Makes Bot leave VC
-> On leave, clears queue and deletes files
'''
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    global voice_controller
    if ctx.author.name == voice_controller:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
            voice_controller = None
            for item in queue:
                filename = item.split(';')[0]
                os.remove(filename)
            queue.clear()

        else:
            await ctx.send("Im not connected to a voice channel!")
    else:
        await ctx.send(f'Sorry {ctx.author.name}, only {voice_controller} can tell me to leave!')

'''
Bot Start Music Command
-> Starts playing the music thats in the queue, sends song name
-> If already playing, let em know
-> If nothing to play, let em know
-> If not connected to a VC, let em know
-> Send any exceptions to journal
'''
@bot.command(name='start', help='To play song')
async def start(ctx):
    #global stop_event
    try:
        try:
            #stop_event.clear()
            voice_client = ctx.message.guild.voice_client
            server = ctx.message.guild
            
            if voice_client.is_playing():
                await ctx.send('There is already music playing!')
                return
            elif len(queue) > 0:
                while len(queue) > 0:
                    item = queue[0]
                    items = item.split(';')
                    filename = items[0]
                    title = items[1]
                    duration = items[3]
                    voice_client.play(discord.FFmpegPCMAudio(source=filename))
                    playing_filenames[server.id] = filename
                    await ctx.send('**Now playing:** {}'.format(title))
                    guild_id = server.id
                    filename = playing_filenames.get(guild_id)
                    
                    await asyncio.sleep(int(duration)+5)
                
                    if os.path.exists(filename):
                        os.remove(filename)
                        del playing_filenames[guild_id]
                        cout = 0
                        for i in queue:
                            if filename in i:
                                queue.pop(cout)
                            else:
                                pass
                            cout += 1
            else:
                await ctx.send('There is nothing to play!')

        except IndexError as e:
            pass
        except Exception as a:
            await ctx.send("I'm not connected to a voice channel!")
    except Exception as a:
                    journal.send(a)

'''
Bot Stop Song Command
-> Stops and Removes the currently playing song
-> If theres nothing playing, let em know
-> If its not the assigned user, let em know
'''
@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    controller = queue[0].split(';')[2]
    journal.send(controller)
    if controller == ctx.author.name:
        if voice_client.is_playing():
            voice_client.stop()
            guild_id = server.id
            filename = playing_filenames.get(guild_id)
            if os.path.exists(filename):
                os.remove(filename)
                del playing_filenames[guild_id]
                if queue:
                    queue.pop(0)
        else:
            await ctx.send("There's nothing playing at the moment.")
    else:
        await ctx.send(f'Sorry {ctx.mention}, control of this track belongs to {controller}.')

'''
Bot Queue Song Command
-> Downloads user specified YT link
-> Converts downloaded file to discord VC audio
-> Adds file to queue and assigns user to song
-> If longer than 8 minutes, let em know
-> If queue is full, let em know
-> If the link isnt supported, let em know
-> If the bot isnt connected to a VC, let em knoe
'''
@bot.command(name='q', help='Queues a song')
async def queue_song(ctx, url):
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        try:
            filename, title, duration = await YTDLSource.from_url(url, loop=bot.loop)
        except Exception as e:
            journal.send(e)
             if int(duration) < 480:
            source = discord.FFmpegPCMAudio(source=filename)

            if len(queue) >= 10:
                await ctx.send('Sorry, only 10 songs are allowed in the queue at a time.')
                return
            else:
                queue.append(filename+";"+title+";"+ctx.author.name+";"+duration)
                await ctx.send(f'{ctx.author.name} added {title} to the queue!')
        else:
            await ctx.send(f'Sorry {ctx.author.name}, only songs under 8 minutes are allowed.')
            os.remove(filename)
        await ctx.message.delete()
    except youtube_dl.utils.DownloadError as e:
        await ctx.send("That link isnt supported.")
    except Exception as et:
        journal.send(et)
        await ctx.send("Im not connected to a voice channel!")

'''
Bot Display Queue Command
-> Displays the music queue in the called server
-> If theres nothing playing, let em know
-> If its not the assigned user, let em know
'''
@bot.command(name='lsq', help='Displays the queue')
async def list_queue(ctx):
    if queue:
        queue_items = [song.split(';')[1] for song in queue]
        queue_list = "\n‣ ".join(queue_items)
        await ctx.send(f'**Queue**```\n‣ {queue_list}```')
    else:
        await ctx.send('There is no queue list available.')
   
'''
Bot Display Commands
-> Displays the different commands a user can use
'''
@bot.command(name='help', help='Displays help page')
async def help(ctx):
    text = (
        "**Commands**```\n\n"
        "!help\n- Shows this message\n\n"
        "!roles\n- Lists all roles on the server\n\n"
        "!role \"[role]\"\n- Assigns specified role to the user\n\n"
        "!rmrole \"[role]\"\n- Removes specified role from user\n\n"
        "!sub\n- Subscribes user to announcements\n\n"
        "!unsub\n- Unsubscribes user from getting announcements\n\n"
        "!rmrole \"[role]\"\n- Removes specified role from user\n\n"
        "!suggest \"[suggestion]\"\n- Make a /suggestion\n\n"
        "!thanks\n- Give R2D2 your thanks\n\n"
        "!random [gif, pic, vuln, fact, movie, song]\n- Recieve a random gif, pic, vulnerability, fact, movie, or song\n\n"
        "!submit [gif, pic, vuln, fact, movie, song] [link, text, pic, gif]\n- Submit an image, CVE, fact, movie, or song to add to the !random command\n\n"
        "!join\n- Make R2 Jukebox join your voice channel\n\n"
        "!leave\n- Instruct R2 to leave the current voice channel\n\n"
        "!q [youtube link]\n- Submit a song to the jukebox queue\n\n"
        "!lsq\n- View the current song queue\n\n"
        "!start\n- Start the jukebox\n\n"
        "!stop\n- Stop the jukebox\n\n"

        "```\n"
        "*Not all random categories are currently available*\n*Please make sure to use quotes where necessary!*\n"
    )
    await ctx.send(text)

'''
Bot Display Roles Command
-> Displays the roles available to the user
-> Else is a fallback message, error out
'''
@bot.command(name='roles', help='Displays the roles available to users')
async def list_roles(ctx):
    server_roles = [role for role in ctx.guild.roles if not role.is_default()]

    if server_roles:
        role_names = [role.name for role in server_roles if role.name not in restricted_roles]
        role_list = "\n‣ ".join(role_names)

        await ctx.send(f'**Available roles**```\n‣ {role_list}```')
    else:
        await ctx.send('There are no additional roles on this server.')

'''
Bot Assign Role Command
-> Assigns role to a user with a command, cant be in restricted roles
-> If role is already assigned, let em know
-> If role doesnt exist, let em know
'''
@bot.command(name='role', help='Gives role to asking user')
async def assign_role(ctx, role_name):
    if role_name.lower() in restricted_roles:
        await ctx.send(f'{role_name.lower()} is not allowed to be assigned!')
        return

    role = None
    for guild_role in ctx.guild.roles:
       if guild_role.name.lower() == role_name.lower():
            role = guild_role
            break

    if role:
        if any(r.id == role.id for r in ctx.author.roles):
            await ctx.send(f'You already have the role: {role_name.lower()}!')
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f'You\'ve been assigned the role: {role_name.lower()}!')
                else:
        await ctx.send(f'Sorry, {role_name} wasn\'t found in the server roles.')

'''
Bot Remove Role Command
-> Removes specified role from asking user
-> If the role is restricted, let em know
-> If the role doesnt exist, let em know
-> If the role isnt assigned to the user, let em know
'''
@bot.command(name='rmrole', help='Removes role from asking user')
async def remove_role(ctx, role_name):
    role = None
    if role_name.lower() not in restricted_roles:
        #role = discord.utils.get(ctx.guild.roles, name=lambda r: r.name.lower() == role_name.lower())
        for grole in ctx.guild.roles:
            if grole.name.lower() == role_name.lower():
                role = grole
        if role:
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
                await ctx.send(f'{role_name} has been removed!')
            else:
                await ctx.send(f'Sorry, you\'re not assigned the role {role_name}.')
        else:
            await ctx.send(f'Sorry, {role_name} can\'t be found in the server roles.')
    elif role_name.lower() not in [role.name.lower() for role in ctx.guild.roles if not role.is_default()]:
        await ctx.send(f'{role_name} does\'nt exist!')
    else:
        await ctx.send(f'Sorry, you can\'t remove that role.')

'''
Bot Subscribe Command
-> Subscribes user to announcements
-> If already subbed, let em know
'''
@bot.command(name='sub', help='Subscribes users to announcements')
async def subscribe(ctx):
    # TODO: fix indent
        try:
                role = discord.utils.get(ctx.guild.roles, name='announcements')
                if role in ctx.author.roles:
                        await ctx.send(f'You are already subscribed!')
                else:
                        await ctx.author.add_roles(role)
                        await ctx.send(f'You\'ve been subscribed!')
        except Exception as e:
                journal.send(f'ERROR subscribe: {e}')

'''
Bot Unsubscribe Command
-> Unsubscribes user to announcements
-> If already unsubbed, let em know
'''
@bot.command(name='unsub', help='Unsubscribes users from announcements')
async def unsubscribe(ctx):
    try:
        role = discord.utils.get(ctx.guild.roles, name='announcements')
        if role not in ctx.author.roles:
            await ctx.send(f'You aren\'t subscribed yet!')
        else:
            await ctx.author.remove_roles(role)
            await ctx.send(f'You\'ve been unsubscribed!')
    except Exception as e:
            journal.send(f'ERROR unsubscribe: {e}')

'''
Bot Create Announcement Command
-> Allows users in a specified channel with specified role to make announcements
-> If contains bad char, let em know
-> Errors go to journalctl
'''
@bot.command(name='announce', help='creates an announcement through r2')
async def announce(ctx,  *, announcement: str):
    try:
        if ctx.channel.id != CATHID:
            return
        role = discord.utils.get(ctx.guild.roles, name='warden')
        if role not in ctx.author.roles:
            return
        else:
            allowed_characters_pattern = r'[\w\s.!?,:;\'"“”&=/%-]+'
            if not re.match(allowed_characters_pattern, announcement):
                await ctx.send('Your announcement contains an illegal character, please review it and try again.')
                return
            # This announcement should only be made in a specified channel
            #await bot.get_channel().send(f'@announcements {announcement}') #
            channel = bot.get_channel(ANNOID)
            ann_role = discord.utils.get(ctx.guild.roles, name='announcements')
            await channel.send(f'{ann_role.mention} {announcement}')
    except Exception as e:
        journal.send(f'ERROR announce: {e}')


'''
Bot Suggest Feature Command
-> Allows users to suggest features for the server & writes to log file in specified path
-> If contains bad char, let em know
'''
@bot.command(name='suggest', help='Send in a suggestion')
async def suggest(ctx, *, suggestion: str):

    suggestion = suggestion.strip()

    allowed_characters_pattern = r'^[A-Za-z0-9.!? ,“”""<>()]+$'
    if not re.match(allowed_characters_pattern, suggestion):
        await ctx.send('Your suggestion contains an illegal character, please review it and try again.')
        return

    user = ctx.author.name
    date = datetime.now().strftime('%m-%d-%Y')
    file_path = WPATH+'/SUBMIT/suggestions.txt'

    with open(file_path, 'a') as file:
        file.write(f'User: {user}\nDate: {date}\nSuggestion: {suggestion}\n\n')

    await ctx.send('Thanks for your input! Its been recorded and will be looked at soon!')

'''
Bot Submit Artifact Command
-> Allows users to submit artifacts, does not auto download.
-> Saves jump link to log in specified path
-> If user didnt select a valid category to submit to, let em know
-> If something went wrong let the user know, and create log of error
-> If submit success, let em know
'''
@bot.command(name="submit", help="submit [gif, pic, vuln, fact, movie, song] [link, text, pic, gif]")
async def random_item(ctx, cate, *text):
    # TODO: Add case id and ability for user to look at the status of the case
    cates = ["gif","pic","movie","song"]
    if cate.strip() not in cates:
        await ctx.send('Sorry, thats not a valid category to choose from.')
    else:
        try:
            user = ctx.author.name
            date = datetime.now().strftime('%m-%d-%Y')
            header = (f'{cate.strip().upper()} SUBMISSION BY {user} DATE: {date}\n')
            sent_text = (' '.join(text))
            if sent_text == '':
                sent_text = '**NO TEXT TO DISPLAY**'
            else:
                pattern = r'[^A-Za-z0-9.,=!?/:\\ -]'
                sent_text =  re.sub(pattern, '', sent_text)

            # Open categories submission files for writing or create log of error.
            if cate.strip() == 'gif':
                file_path = WPATH+'/SUBMIT/gifSub.txt'
            elif cate.strip() == 'pic':
                file_path = WPATH+'/SUBMIT/picSub.txt'
            elif cate.strip() == 'song':
                file_path = WPATH+'/SUBMIT/songSub.txt'
            elif cate.strip() == 'movie':
                file_path = WPATH+'/SUBMIT/movieSub.txt'
            else:
                date = datetime.now().strftime('%m-%d-%Y [%I:%M:%S%p]')
                with open(WPATH+'/LOGS/botLog.txt', 'a') as file:
                    file.write(f'Something went wrong when user called SUBMIT {date}.\nCommand: !submit {cate} {sent_text}\n\n')
                    await ctx.send('Something went wrong but a technician will check it out soon.')



            with open(file_path, 'a') as file:
                file.write(f'{header}{sent_text}\nJUMP LINK:{ctx.message.jump_url}\n\n')
            await ctx.send('Thanks for your submission! The council will now decide your fate.')
        except Exception as e:
            journal.send()

'''
Bot Random Artifact Command
-> Allows users query R2s DB for a random artifact from a specified category
-> If category isnt valid, let em know
-> If category isnt built yet, let em know
'''
@bot.command(name="random", help="random [gif, pic, vuln, fact, movie, song]")
async def random_item(ctx, cate):
    cates = ["gif","pic","vuln","fact","movie","song"]
    if cate not in cates:
        await ctx.send('Sorry, thats not a valid category to choose from.')
    else:
        if cate == 'gif':
            gl = []
            for file in (os.listdir(str(WPATH)+'/GIFS/')):
                gl.append(file)
            await ctx.send(file=discord.File(str(WPATH+'/GIFS/'+random.choice(gl))))
        elif cate == 'pic':
            gl = []
            for file in (os.listdir(str(WPATH)+'/PICS/')):
                gl.append(file)
            await ctx.send(file=discord.File(str(WPATH+'/PICS/'+random.choice(gl))))
        else:
            await ctx.send('Sorry, this category isn\'t available yet.')

'''
Bot Hacker Quote
-> Mess with the best...
'''
@bot.command(name='hackers', help='Mess with me')
async def hackers(ctx):
    await ctx.send('Incoming Transmission from Zero Cool:')
    t.sleep(2)
    await ctx.send('Mess with the best...')
    t.sleep(0.5)
    await ctx.send('Die like the rest.')
    t.sleep(0.5)
    await ctx.send('Hack the planet!')

'''
Bot Troll Detected
-> Roger Roger
'''
@bot.command(name='trolldetected', help='blastem!')
async def hackers(ctx):
    await ctx.send('🚨 TROLL DETECTED 🚨')
    t.sleep(1)
    await ctx.send('💥 BLAST \'EM 💥')

'''
Bot Ping
-> Ping, Pong
'''
@bot.command(name='beep', help='beep boop')
async def beep(ctx):
    await ctx.send('boop')

'''
Bot Thanks
-> +1 Charisma
'''
@bot.command(name='thanks', help='give thanks')
async def thanks(ctx):
    await ctx.send(random.choice(R2))

'''
Bot Exploit
-> Unused Feature
'''
@bot.command(name='exploit', help='Sends a random well-known vulnerability/exploit')
async def beep(ctx):
    await ctx.send('boop')

'''
Bot Startup Events
-> Runs announce events method from announceEventsController
-> Runs member retrival method from memberWatchController
-> Sends status to journal
'''
@bot.event
async def on_ready():
    announce_events.start()
    await get_members()
    journal.send('Goodmornin')
    change_bot_status.start()

'''
Bot Catch Errors
-> Catches event name and subsequent error
-> Posts traceback in journal
'''
@bot.event
async def on_error(event, *args, **kwargs):
    import traceback
    error_message = traceback.format_exc()
    journal.send(f"Error in {event}: {error_message}")

'''
Member Join Listener
-> Listens for member joing and sends welcome message
-> Adds role "user" to new members
-> Adds user to known users list
'''
@bot.event
async def on_member_join(ctx):
    channel = bot.get_channel(WELCID)
    await channel.send(file=discord.File(str(WPATH+'/GIFS/42.gif')))
    await channel.send(f'{ctx.mention}, just warped in! We\'re excited to have you!\n\nWe have some rules on this starship that we use maintain a healthy community; We trust
 you will abide by them:\n1. Be respectful\n2. No NSFW\n3. If you wouldn\'t do it on campus don\'t do it here\n4. We hack stuff, but keep it legal.\n5. Don\'t block @wardens
 \n6. Have a blast and party on!\n\nIf you have any issues arise with other users or with how you\'re being treated here or in class, please feel free to reach out to a @war
den!\n\nAlso, don\'t forget to visit <#1159474132866564167> to try out our bot and assign yourself some roles!\n\n@everyone be sure to give {ctx.name} a warm welcome! :wave:
')
    role = discord.utils.get(ctx.guild.roles, name='user')
    await ctx.add_roles(role)
    with open(str(WPATH+'/LOGS/userlist.txt'),'a') as userlist:
        user_id = ctx.id
        userlist.write(str(user_id)+'\n')

'''
VC Status Listener
-> If VC is empty, stop music, cleanup, and leave
'''
@bot.event
async def on_voice_state_update(ctx, before, after):
    try:
        if ctx.guild.voice_client and len(ctx.guild.voice_client.channel.members) == 1:
            ctx.guild.voice_client.stop()
            for item in queue:
                filename = item.split(';')[0]
                os.remove(filename)
            queue.clear()
            await ctx.guild.voice_client.disconnect()
    except:
        journal.send("Not able to disconnect.")

async def update_events():
    guild_id = SERVID
    try:
        stored_events = await retrieve_events()
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
                        journal.send(f'Writing: {schevent}')
                        await write_event(f'{event.name};;{formatted_time};;false;;false;;false')
                        continue
                    else:
                        pass

            for stored_event in stored_events:
                    if stored_event.replace(';;false', '').replace(';;true', '') not in form_events:
                        journal.send(f'Removing: {stored_event}')
                        await remove_event(stored_event)
                    else:
                        pass
        else:
                journal.send(f'No guild found')
    except Exception as e:
            journal.send(f'ERROR update_events: {e}')

async def retrieve_events():
        scheduled_events = []
        try:
            with open((WPATH+'/schevents.txt'), 'r') as schevents:
                for event in schevents:
                    scheduled_events.append(event.strip())
        except Exception as e:
            journal.send(f'ERROR retrieve_event: {e}')
        finally:
            return scheduled_events

async def write_event(event):
        try:
            with open((WPATH+'/schevents.txt'), 'a') as schevents:
                schevents.write(event+'\n')
        except Exception as e:
            journal.send(f'ERROR write_event: {e}')

async def remove_event(event):
        try:
            with open((WPATH+'/schevents.txt'), 'r') as schevents:
                scheduled_events = schevents.readlines()

            with open((WPATH+'/schevents.txt'), 'w') as schevents:
                for schevent in scheduled_events:
                    if schevent.strip() != event:
                        schevents.write(schevent)
        except Exception as e:
            journal.send(f'ERROR remove_event: {e}')
            
async def update_event(event, mode):
        try:
            await remove_event(event)
            split_event = event.split(";;")
            # Mode selected is one week
            if mode == '1':
                await write_event(f'{split_event[0]};;{split_event[1]};;true;;{split_event[3]};;{split_event[4]}')
            # Mode selected is one day
            elif mode == '2':
                await write_event(f'{split_event[0]};;{split_event[1]};;{split_event[2]};;true;;{split_event[4]}')
            # Mode selected is three day
            elif mode == '3':
                await write_event(f'{split_event[0]};;{split_event[1]};;{split_event[2]};;{split_event[3]};;true')
        except Exception as e:
            journal.send(f'ERROR update_event: {e}')

'''
Member Join Offline Compensator
-> Checks if all users in server have been accounted for
-> Depending on # of missed users, either joint welcome or single
-> Saves new users to member list
'''
# TODO: This will need a better sorting algorithm and is literally frankensteins monster
async def get_members():
    planets = ['Zeffo','Tatooine','Endor','Kamino','Jakku','Kashyyyk','Alderaan','Mustafar','Tinnel IV','Saki','Rion','Ojom','Naboo','Naraka','Ando','Affadar','Aargonar']
    guild_id = SERVID
    guild = bot.get_guild(guild_id)
    channel = bot.get_channel(WELCID)
    file_path = WPATH+'/LOGS/userlist.txt'
    users_to_add = {}
    # Read user list, if file doesnt exist, make it
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
        if str(user_id)+'\n' not in users:
            users_to_add[str(user)] = (user_id)
    # If there are new members
    if len(users_to_add) >= 1:
        # If theres only one new member
        if len(users_to_add) == 1:
            member = guild.get_member_named(next(iter(users_to_add)))
            # SENDING WELCOME TO SINGLE
            await channel.send(f"Boop beep, Hello there {member.mention}!\n\nWe must've picked you up near the planet {random.choice(planets)} while I was recharging! I hope
 @everyone gave you a warm welcome while I was gone!\n\nWhile i'm here, we have some rules on this starship that we use maintain a healthy community; We trust you will abide
 by them:\n1. Be respectful\n2. No NSFW\n3. If you wouldn\'t do it on campus don\'t do it here\n4. We hack stuff, but keep it legal.\n5. Don\'t block @wardens \n6. Have a bl
ast and party on!\n\nIf you have any issues arise with other users or with how you\'re being treated here or in class, please feel free to reach out to a @warden!\n\nAlso, d
on\'t forget to visit <#1159474132866564167> to try out our bot and assign yourself some roles!\n\n@everyone if you haven\'t, be sure to give {member.mention} a warm welcome
! :wave:")
        else:
            cnt = 1
            message = "Beep boop, Hello there "
            for user, user_id in users_to_add.items():
                if cnt == len(users_to_add):
                    message = message + f'and {guild.get_member_named(user).mention}!'
                # Handles only two new people
                elif len(users_to_add) == 2:
                    message = message + f'{guild.get_member_named(user).mention} '
                else:
                    message = message + f'{guild.get_member_named(user).mention}, '
                cnt += 1
            message = message + "\n\nIt seems I missed you while I was recharging! I hope @everyone gave you a warm welcome while I was gone!\n\nWhile i'm here, we have some
 rules on this starship that we use maintain a healthy community; We trust you will abide by them:\n1. Be respectful\n2. No NSFW\n3. If you wouldn\'t do it on campus don\'t 
do it here\n4. We hack stuff, but keep it legal.\n5. Don\'t block @wardens \n6. Have a blast and party on!\n\nIf you have any issues arise with other users or with how you\'
re being treated here or in class, please feel free to reach out to a @warden!\n\nAlso, don\'t forget to visit <#1159474132866564167> to try out our bot and assign yourself 
some roles!\n\n@everyone if you haven't, be sure to give these recruits a warm welcome! :wave:"
            # SENDING WELCOME TO MULTIPLE
            await channel.send(f'{message}')

        # Modify the saved user list
        with open(file_path, 'a') as user_file:
            for user, user_id in users_to_add.items():
                user_file.write(str(user_id)+'\n')


#################################################
# TASKS +++++++++++++++++++++++++++++++++++++++++
#################################################

@tasks.loop(seconds=3600)
async def announce_events():
    #journal.send('Trying announce_events')
    ## Should only execute if it is 11am-11:59am
    if str(datetime.now().hour) == '11':
        journal.send('Running announcements')
        try:
            stored_events = await retrieve_events()
            await update_events()
            current_date = datetime.now()

            for event in stored_events:
                # Log
                journal.send(f'Testing: {event}')

                date = event.split(';;')[1].split(' ')[0]
                
                # Month of event matches
                if date.split('/')[0] == str("{:02d}".format(current_date.month)):

                    # Getting a few variables.
                    channel = bot.get_channel(ANNOID) # remove ctx
                    role = discord.utils.get(bot.get_guild(SERVID).roles, name='announcements')
                    d = date.split('/')[1]
                    n = event.split(';;')[0]
                    t = event.split(';;')[1].split(' ')[1]
                    time_span = ['in one week', 'in three days', 'tomorrow'] # Need to update how events are stored
                    LP_link = 'https://www.eventbrite.com/e/lockpicking-learners-group-tickets-707450733187'

                    # Log
                    journal.send(f'Retrieved Role: {role} Day: {d} Event: {n}')
                    
                    # Crafing Announcmement to be made, if any
                    msg = await craft_announcement(role, n, t, d, time_span, LP_link, current_date, event)

                    # Sending annnouncement to announcmeent channel
                    if msg != None:
                        await channel.send(msg)

        except Exception as e:
            journal.send(f'ERROR announce_events: {e}')

@tasks.loop(seconds=5400)
async def change_bot_status():
    journal.send('Executing Status Change')
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


    activities = [discord.Activity(type=discord.ActivityType.listening, name=random.choice(sample_songs)),
    discord.Activity(type=discord.ActivityType.watching, name=random.choice(sample_movies)),
    discord.Game(name=random.choice(sample_games))]

    await bot.change_presence(activity=random.choice(activities))


async def craft_announcement(role, n, t, d, time_span, LP_link, current_date, event):

    ann_to_send = None

    # Grabbing the right time span choice
    time_span_choice = await get_time_span_choice(time_span, d, current_date, n, event)

    # Converting time
    t = await convert_time(t)

    DC_location = 'The Daily Growler'

    DC_templates = [ f'{role.mention} Hey hackers and cyber pals! Join us for {n}, happening **{time_span_choice}** at **{t}**. It\'s gonna be a super laid-back hangout wher
e we\'ll chat about hacking, share cool demos, and maybe even crack a few jokes (or codes). So mark your calendars and come chill with us! Don\'t forget, it\'s all happening
 at {DC_location}.', 
    f'{role.mention} Psst... Heard about {n}? It\'s THE place to be for hackers and security enthusiasts! We\'re meeting up **{time_span_choice}** at **{t}** for a casual ev
ening filled with hacking talks, demos, and just good ol\' hangs. Swing by and let\'s geek out together. See you there!', 
    f'{role.mention} Ready to unwind with fellow hackers? {n} is happening **{time_span_choice}** at **{t}**, and you\'re invited! We\'ll have hacking demos, discussions, an
d plenty of snacks. Whether you\'re a seasoned hacker or just curious about cybersecurity, come join the fun. Let\'s kick back and hack away!', 
    f'{role.mention} Hey hackers, looking for a laid-back evening with like-minded folks? Look no further than {n}! Join us **{time_span_choice}** at **{t}** for a casual ga
thering of security enthusiasts. We\'ll have hacking talks, maybe a few impromptu demos, and plenty of laughs. Come hang out with us and enjoy some good vibes!', 
    f'{role.mention} Calling all hackers and cyber enthusiasts! {n} is happening **{time_span_choice}** at **{t}**, and it\'s gonna be lit (in a chill way, of course). We\'l
l have hacking discussions, maybe a mini CTF, and lots of friendly faces. So grab your hoodie and your favorite beverage, and let\'s hack and chill together!' ]
    
    LP_templates = [ f'{role.mention} Hey fellow physical security enthusiasts! Get ready for a chill lockpicking meetup happening soon. Join us for {n} **{time_span_choice}
** at **{t}** for a relaxed evening of picking, chatting, and sharing tips. Don\'t forget to grab your lockpicks and get your ticket here: {LP_link}. See you there!', 
    f'{role.mention} Hey lockpickers, it\'s meetup time! Join us for {n} **{time_span_choice}** at **{t}** for an evening filled with picking, learning, and good vibes. Brin
g your favorite locks and join the fun! Don\'t forget to snag your ticket before they\'re gone: {LP_link}. See you at the meetup!', 
    f'{role.mention} Looking for a relaxed lockpicking session with friendly faces? Look no further! {n} is coming up **{time_span_choice}** at **{t}** for an evening of pic
king locks and making new friends. Reserve your spot by getting your ticket here: {LP_link}. Let\'s have a lockpicking party!', 
    f'{role.mention} Lockpickers, unite! There\'s a casual meetup happening **{time_span_choice}** at **{t}**, and you\'re invited. Whether you\'re a lockpicking newbie or a
 seasoned pro, come hang out with us for a fun night of picking and chatting. Don\'t miss out – secure your ticket and let\'s get picking! {LP_link}' ]


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
                journal.send('Something went wrong when attempting to grab an announcment. See craft_announcement.')

            ann_to_send = 'Testing Announcement System... Please Stand By...'

        else:
            ann_to_send = f'{role.mention} {n} is coming up **{time_span_choice}**! Be sure to check out the details in the events tab if you\'re interested!'

    return ann_to_send

'''
Time Converter
-> Converts Military time to standard
'''
async def convert_time(time):
    try:
        mil_time = datetime.strptime(time, "%H:%M")
        std_time = mil_time.strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return '12:00 AM'
    except Exception as e:
        journal.send(f'Error in convert_time: {e}')
    return std_time

async def get_time_span_choice(time_span, day, current_date, n, event):
    # This function also acts as a check if theres even an announcment to be given

    time_span_choice = None

    # If today is one week before
    if str((int(day) - 8)) == str(current_date.day):
        # LOG
        journal.send(f'Event {n} is one week before')
        if event.split(';;')[3] != 'true':
            time_span_choice = time_span[0]
            await update_event(event, '1')

    # If today is one before
    elif str(int(day)-1) == str(current_date.day):
        # LOG
        journal.send(f'Event {n} is tommorow')
        if event.split(';;')[3] != 'true':
            time_span_choice = time_span[2]
            await update_event(event, '2')

    # If today is three before
    elif str(int(day)-3) == str(current_date.day):
        # LOG
        journal.send(f'Event {n} is 3 days before')
        if event.split(';;')[3] != 'true':
            time_span_choice = time_span[1]
            await update_event(event, '3')

    return time_span_choice

'''
Main Routine
-> Begings bot loop
-> Writes any startup errors to service journal 
-> Runs Cleanup method from musicController to remove leftover files
'''
if __name__=="__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        journal.send(f"Something went wrong when initializing the bot: {e}")
    finally:
        cleanup_end()
