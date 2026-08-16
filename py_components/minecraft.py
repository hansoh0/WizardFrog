"""
Minecraft server status:

_format_player_list():
Joins a list of player names into "a, b and c" (oxford comma style)

mcstatus():
!mcstatus - Async queries MC_SERVER_ADDRESS and replies with whether the
server is up/down and who's currently in-game
"""

from mcstatus import JavaServer

from bot_instance import bot
from config import MC_SERVER_ADDRESS


def _format_player_list(names):
    """
    Player Name List Formatter
    -> Joins a list of names into "a, b and c" (Oxford-comma style)
    """
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"


@bot.command(name='mcstatus', help='Checks the Minecraft server status')
async def mcstatus(ctx):
    """
    Bot Minecraft Status Command
    -> Queries MC_SERVER_ADDRESS asynchronously so a slow/unreachable server doesn't block the bot
    -> If unreachable, let em know its down
    -> If reachable, reports online count and who's currently in-game
    """
    try:
        server = await JavaServer.async_lookup(MC_SERVER_ADDRESS)
        status = await server.async_status()
    except Exception:
        await ctx.send("The server is not responding and may be DOWN.")
        return

    online = status.players.online
    if online == 0:
        await ctx.send("No one is online, but the server is UP.")
    elif status.players.sample:
        names = _format_player_list([player.name for player in status.players.sample])
        verb = "is" if online == 1 else "are"
        await ctx.send(f"The server is UP and {names} {verb} currently in-game.")
    else:
        await ctx.send(f"The server is UP with {online} player(s) online.")
