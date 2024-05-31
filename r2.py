#! /usr/bin/python3

import os, discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import yt_dlp as youtube_dl
import traceback

load_dotenv()
# TODO: Add queue > cant play if queue not empty
# need new token
TOKEN = ""
intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents, help_command=None)
queue = []
playing_filenames = {}
restricted_roles = ["king of the hill","glados"]

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
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        title = data.get('title')
        return filename, title

class FileCleanup:
    def __init__(self, filename):
        self.filename = filename

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            os.remove(self.filename)
        except Exception as e:
            print(f"Error deleting file: {e}")

@bot.command(name='help', help='Displays help page')
async def help(ctx):
    text = (
    "**Help Menu**```\n\n"
    "!help           Shows this message\n"
    "!join           Instructs the bot to join your voice channel\n"
    "!leave          Instructs the bot to leave the voice channel\n"
    "!play [link]    Plays the linked song (Youtube)\n"
    "!queue [link]   Adds linked song to the queue\n"
    "!vqueue         Shows the current queue\n"
    "!song           Displays the currently playing song\n"
    "!lsroles        Lists all roles on the server\n"
    "!role [role]    Assigns specified role to the user\n"
    "!rmrole [role]  Removes specified role from user\n"
    "```\n"
)
    await ctx.send(text)

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if ctx.guild.voice_client is not None:
        await ctx.send(f'Sorry, im already hanging out in {ctx.guild.voice_client.channel.mention}.')
        return
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("Im not connected to a voice channel!")

@bot.command(name='play', help='To play song')
async def play(ctx, url):
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client

        if len(queue) > 0:
            await ctx.send('Sorry, there are items in the queue right now.')
            return
        else:    
            async with ctx.typing():
                filename, title = await YTDLSource.from_url(url, loop=bot.loop)
                voice_channel.play(discord.FFmpegPCMAudio(source=filename))
            playing_filenames[server.id] = filename
            await ctx.send('**Now playing:** {}'.format(title))

            async with FileCleanup(filename):
                pass
    except youtube_dl.utils.DownloadError as e:
        await ctx.send("That link isnt supported.")
    except:
        await ctx.send("Im not connected to a voice channel!")

@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send("There's nothing playing at the moment.")
    
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("There's nothing playing at the moment.")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    if voice_client.is_playing():
        voice_client.stop()

        guild_id = server.id
        filename = playing_filenames.get(guild_id)
        if os.path.exists(filename):
            os.remove(filename)
            del playing_filenames[guild_id]

        if queue:
            queue.pop(0)
            await play_next(ctx)

    else:
        await ctx.send("There's nothing playing at the moment.")

@bot.command(name='lsroles', help='Displays the roles available to users')
async def list_roles(ctx):
    server_roles = [role for role in ctx.guild.roles if not role.is_default()]

    if server_roles:
        role_names = [role.name for role in server_roles if role.name != "glados"]
        role_list = "\n‣ ".join(role_names)

        await ctx.send(f'**Available roles**```\n‣ {role_list}```')
    else:
        await ctx.send('There are no additional roles on this server.')

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
        await ctx.author.add_roles(role)
        await ctx.send(f'You\'ve been assigned the role: {role_name.lower()}!')
    else:
        await ctx.send(f'Sorry, {role_name} wasn\'t found here.')

@bot.command(name='rmrole', help='Removes role from asking user')
async def remove_role(ctx, role_name):
    if role_name.lower() not in restricted_roles:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await ctx.author.remove_roles(role)
            await ctx.send(f'{role_name} has been removed!')
        else:
            await ctx.send(f'Sorry, you\'re not assigned {role_name}.')
    elif role_name.lower() not in [role.name.lower() for role in ctx.guild.roles if not role.is_default()]:
        await ctx.send(f'{role_name} does\'nt exist!')
    else:
        await ctx.send(f'Sorry, you can\'t remove that role.')

@bot.command(name='queue', help='Queues a song')
async def queue(ctx, url):
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        filename, title = await YTDLSource.from_url(url, loop=bot.loop)
        source = FFmpegPCMAudio(source=filename)

        if len(queue) >= 5:
            await ctx.send('Sorry, only 5 songs are allowed in the queue at a time.')
            return
        else:
            queue.append(source)
            await ctx.send(f'{title} added to queue.')
    except youtube_dl.utils.DownloadError as e:
        await ctx.send("That link isnt supported.")
    except:
        await ctx.send("Im not connected to a voice channel!")

@bot.event
async def on_voice_state_update(member, before, after):
    # Check if everyone left the voice channel and clear the queue
    if member.guild.voice_client and len(member.guild.voice_client.channel.members) == 1:
        member.guild.voice_client.stop()
        queue.clear()
        await member.guild.voice_client.disconnect()

if __name__ == "__main__" :
    bot.run(TOKEN)
