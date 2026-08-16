"""
Role management and announcement subscription commands:

list_roles():
!roles - Lists all assignable (non restricted) roles on the server

assign_role():
!role "[role]" - Assigns a role to the caller if it isn't restricted

remove_role():
!rmrole "[role]" - Removes a role from the caller if it isn't restricted

subscribe():
!sub - Adds the Announcements role to the caller

unsubscribe():
!unsub - Removes the Announcements role from the caller
"""

import discord

from bot_instance import bot
from config import restricted_roles

_restricted_roles_lower = {role.lower() for role in restricted_roles}


@bot.command(name='roles', help='Displays the roles available to users')
async def list_roles(ctx):
    """
    Bot Display Roles Command
    -> Displays the roles available to the user
    -> Else is a fallback message, error out
    """
    server_roles = [role for role in ctx.guild.roles if not role.is_default()]

    if server_roles:
        role_names = [role.name for role in server_roles if role.name not in restricted_roles]
        role_list = "\n‣ ".join(role_names)

        await ctx.send(f'**Available roles**```\n‣ {role_list}```')
    else:
        await ctx.send('There are no additional roles on this server.')


@bot.command(name='role', help='Gives role to asking user')
async def assign_role(ctx, role_name):
    """
    Bot Assign Role Command
    -> Assigns role to a user with a command, cant be in restricted roles
    -> If role is already assigned, let em know
    -> If role doesnt exist, let em know
    """
    if role_name.lower() in _restricted_roles_lower:
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


@bot.command(name='rmrole', help='Removes role from asking user')
async def remove_role(ctx, role_name):
    """
    Bot Remove Role Command
    -> Removes specified role from asking user
    -> If the role is restricted, let em know
    -> If the role doesnt exist, let em know
    -> If the role isnt assigned to the user, let em know
    """
    role = None
    if role_name.lower() not in _restricted_roles_lower:
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


@bot.command(name='sub', help='Subscribes users to announcements')
async def subscribe(ctx):
    """
    Bot Subscribe Command
    -> Subscribes user to announcements
    -> If already subbed, let em know
    """
    try:
        role = discord.utils.get(ctx.guild.roles, name='Announcements')
        if role in ctx.author.roles:
            await ctx.send(f'You are already subscribed!')
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f'You\'ve subscribed to be pinged for announcements!')
    except Exception as e:
        print(f'Error subscribing: {e}')
        #print(f'ERROR subscribe: {e}')


@bot.command(name='unsub', help='Unsubscribes users from announcements')
async def unsubscribe(ctx):
    """
    Bot Unsubscribe Command
    -> Unsubscribes user to announcements
    -> If already unsubbed, let em know
    """
    try:
        role = discord.utils.get(ctx.guild.roles, name='Announcements')
        if role not in ctx.author.roles:
            await ctx.send(f'You aren\'t subscribed to announcement pings yet!')
        else:
            await ctx.author.remove_roles(role)
            await ctx.send(f'You will no longer recieve pings for announcements!')
    except Exception as e:
        print(f'ERROR unsubscribe: {e}')
