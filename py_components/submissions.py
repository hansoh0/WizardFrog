"""
User-submitted content: suggestion box, community submissions, and
retrieving a random item from those submission pools:

suggest():
!suggest "[suggestion]" - Writes a suggestion to suggestions.txt

submit_item():
!submit [category] [text] - Writes a gif/pic/song/movie submission (with
a jump link) to that category's submission file

get_random_item():
!random [category] - Sends a random file from GIFS/ or PICS/; other
categories aren't built yet
"""

import os
import random
import re
from datetime import datetime

import discord

from bot_instance import bot
from config import WPATH


@bot.command(name='suggest', help='Send in a suggestion')
async def suggest(ctx, *, suggestion: str):
    """
    Bot Suggest Feature Command
    -> Allows users to suggest features for the server & writes to log file in specified path
    -> If contains bad char, let em know
    """
    suggestion = suggestion.strip()

    allowed_characters_pattern = r'^[A-Za-z0-9.!? ,“”""<>()]+$'
    if not re.match(allowed_characters_pattern, suggestion):
        await ctx.send('Your suggestion contains an illegal character, please review it and try again.')
        return

    user = ctx.author.name
    date = datetime.now().strftime('%m-%d-%Y')
    file_path = WPATH + '/SUBMIT/suggestions.txt'

    with open(file_path, 'a') as file:
        file.write(f'User: {user}\nDate: {date}\nSuggestion: {suggestion}\n\n')

    await ctx.send('Thanks for your input! Its been recorded and will be looked at soon!')


@bot.command(name="submit", help="submit [gif, pic, vuln, fact, movie, song] [link, text, pic, gif]")
async def submit_item(ctx, cate, *text):
    """
    Bot Submit Artifact Command
    -> Allows users to submit artifacts, does not auto download.
    -> Saves jump link to log in specified path
    -> If user didnt select a valid category to submit to, let em know
    -> If something went wrong let the user know, and create log of error
    -> If submit success, let em know
    """
    # TODO: Add case id and ability for user to look at the status of the case
    cates = ["gif", "pic", "movie", "song"]
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
                sent_text = re.sub(pattern, '', sent_text)

            # Open categories submission files for writing or create log of error.
            if cate.strip() == 'gif':
                file_path = WPATH + '/SUBMIT/gifSub.txt'
            elif cate.strip() == 'pic':
                file_path = WPATH + '/SUBMIT/picSub.txt'
            elif cate.strip() == 'song':
                file_path = WPATH + '/SUBMIT/songSub.txt'
            elif cate.strip() == 'movie':
                file_path = WPATH + '/SUBMIT/movieSub.txt'
            else:
                date = datetime.now().strftime('%m-%d-%Y [%I:%M:%S%p]')
                with open(WPATH + '/LOGS/botLog.txt', 'a') as file:
                    file.write(f'Something went wrong when user called SUBMIT {date}.\nCommand: !submit {cate} {sent_text}\n\n')
                    await ctx.send('Something went wrong but a technician will check it out soon.')

            with open(file_path, 'a') as file:
                file.write(f'{header}{sent_text}\nJUMP LINK:{ctx.message.jump_url}\n\n')
            await ctx.send('Thanks for your submission! The council will now decide your fate.')
        except Exception as e:
            print(str(e))


@bot.command(name="random", help="random [gif, pic, vuln, fact, movie, song]")
async def get_random_item(ctx, cate):
    """
    Bot Random Artifact Command
    -> Allows users query R2s DB for a random artifact from a specified category
    -> If category isnt valid, let em know
    -> If category isnt built yet, let em know
    """
    cates = ["gif", "pic", "fact", "movie", "song"]
    if cate not in cates:
        await ctx.send('Sorry, thats not a valid category to choose from.')
    else:
        if cate == 'gif':
            gl = []
            for file in (os.listdir(str(WPATH) + '/GIFS/')):
                gl.append(file)
            await ctx.send(file=discord.File(str(WPATH + '/GIFS/' + random.choice(gl))))
        elif cate == 'pic':
            gl = []
            for file in (os.listdir(str(WPATH) + '/PICS/')):
                gl.append(file)
            await ctx.send(file=discord.File(str(WPATH + '/PICS/' + random.choice(gl))))
        else:
            await ctx.send('Sorry, this category isn\'t available yet.')
