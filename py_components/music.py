"""
Jukebox / voice-channel music playback:

YTDLSource:
discord.py audio source wrapping a yt-dlp download; from_url() does the
actual download and returns (filename, title, duration)

FileCleanup:
Async context manager that deletes a file on exit, used for cleaning up
downloaded audio

cleanup_end():
Deletes any leftover .webm files in JUKE/, run once on bot shutdown

join():
!join - Joins the caller's voice channel

leave():
!leave - Leaves the voice channel and clears the queue (only the caller
who originally joined bot can do this)

start():
!start - Plays through the queue one song at a time

stop():
!stop - Stops the current song and removes it from the queue (only the
user who queued it can do this)

queue_song():
!q [youtube link] - Downloads a YouTube link and adds it to the queue if
it's under 8 minutes and the queue isn't full

list_queue():
!lsq - Lists the titles currently in the queue
"""

import asyncio
import os
import discord
import yt_dlp as youtube_dl

from bot_instance import bot
from config import WPATH

voice_controller = None
queue = []
playing_filenames = {}

youtube_dl.utils.bug_reports_message = lambda *args, **kwargs: ''
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'outtmpl': WPATH + '/JUKE/%(title)s.%(ext)s'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    """YT Download Class"""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""
        self.track_length = data.get('duration', 0)

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        """
        Download From YT URL
        -> Removes events from event db
        -> Returns file, title, duration of downloaded content
        """
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename, data.get('title'), str(data.get('duration', 0))


class FileCleanup:
    """Download Cleanup Catch Class"""

    def __init__(self, filename):
        self.filename = filename

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            os.remove(self.filename)
        except Exception as e:
            print(f"Error deleting file: {e}")


def cleanup_end():
    """
    File remover
    -> Removes all files .webm in JUKE directory in file root
    """
    for item in os.listdir(WPATH + "/JUKE"):
        if item.endswith(".webm"):
            os.remove(WPATH + "/JUKE/" + item)


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    """
    Bot Join VC Command
    -> Makes Bot join callers VC
    -> If caller not in VC, let em know
    -> If Bot in another VC, let em know
    """
    global voice_controller
    try:
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
    except Exception as e:
        print(f'Error when joining VC: {e}')


@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    """
    Bot Leave VC Command
    -> Makes Bot leave VC
    -> On leave, clears queue and deletes files
    """
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


@bot.command(name='start', help='To play song')
async def start(ctx):
    """
    Bot Start Music Command
    -> Starts playing the music thats in the queue, sends song name
    -> If already playing, let em know
    -> If nothing to play, let em know
    -> If not connected to a VC, let em know
    -> Prints any exceptions
    """
    try:
        try:
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

                    await asyncio.sleep(int(duration) + 5)

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
        print(str(a))


@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    """
    Bot Stop Song Command
    -> Stops and Removes the currently playing song
    -> If theres nothing playing, let em know
    -> If its not the assigned user, let em know
    """
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    controller = queue[0].split(';')[2]
    print(controller)
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


@bot.command(name='q', help='Queues a song')
async def queue_song(ctx, url):
    """
    Bot Queue Song Command
    -> Downloads user specified YT link
    -> Converts downloaded file to discord VC audio
    -> Adds file to queue and assigns user to song
    -> If longer than 8 minutes, let em know
    -> If queue is full, let em know
    -> If the link isnt supported, let em know
    -> If the bot isnt connected to a VC, let em knoe
    """
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        try:
            filename, title, duration = await YTDLSource.from_url(url, loop=bot.loop)
        except Exception as e:
            print(str(e))
            await ctx.send("Something went wrong downloading that song.")
            return

        if int(duration) < 480:
            if len(queue) >= 10:
                await ctx.send('Sorry, only 10 songs are allowed in the queue at a time.')
                os.remove(filename)
                return
            else:
                queue.append(filename + ";" + title + ";" + ctx.author.name + ";" + duration)
                await ctx.send(f'{ctx.author.name} added {title} to the queue!')
        else:
            await ctx.send(f'Sorry {ctx.author.name}, only songs under 8 minutes are allowed.')
            os.remove(filename)
        await ctx.message.delete()
    except youtube_dl.utils.DownloadError as e:
        await ctx.send("That link isnt supported.")
    except Exception as et:
        print(f'Error queueing song: {et}')
        await ctx.send("Im not connected to a voice channel!")


@bot.command(name='lsq', help='Displays the queue')
async def list_queue(ctx):
    """
    Bot Display Queue Command
    -> Displays the music queue in the called server
    -> If theres nothing playing, let em know
    -> If its not the assigned user, let em know
    """
    if queue:
        queue_items = [song.split(';')[1] for song in queue]
        queue_list = "\n‣ ".join(queue_items)
        await ctx.send(f'**Queue**```\n‣ {queue_list}```')
    else:
        await ctx.send('There is no queue list available.')
