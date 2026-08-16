"""
Website content-integrity monitor, alerts posted in the CATHID channel:

_is_council():
Helper - true if the command author has the "Council" role

_load_baseline_hashes():
Reads the known-good sha256 per URL from site_hashes.txt

_save_baseline_hash():
Writes/updates one URL's known good hash in site_hashes.txt

_fetch_hash():
Downloads a URL (following redirects) and returns the sha256 of its body

_check_all_sites():
Fetches every SITE_MONITOR_URLS entry, compares it to its baseline, and
alerts once on a down/up transition. The first check for a URL just
records the baseline instead of alerting. Note: since the baseline is
fixed at first checked content rather than the previous check's content,
a deliberate content change will permanently read as "down" until
!resethash is used for that URL.

check_sites():
The 20 minute background loop wrapping _check_all_sites()

check_sites_now():
!checksites - Council-only: runs _check_all_sites() immediately, then
reports every site's current status regardless of whether it changed

reset_hash():
!resethash [url] - Council-only: clears one URL's stored baseline so the
next check records fresh content as the new known-good hash
"""

import hashlib

import aiohttp
import discord
from discord.ext import tasks

from bot_instance import bot
from config import CATHID, SITE_MONITOR_URLS, WPATH

HASH_FILE = WPATH + '/site_hashes.txt'
COUNCIL_ROLE = 'Council'

is_down = {url: False for url in SITE_MONITOR_URLS}


def _is_council(ctx):
    """
    Council Role Checker
    -> Returns True if the invoking user has the "Council" role
    """
    role = discord.utils.get(ctx.guild.roles, name=COUNCIL_ROLE)
    return role in ctx.author.roles


def _load_baseline_hashes():
    """
    Baseline Hash Reader
    -> Reads the known-good sha256 per monitored URL from site_hashes.txt
    """
    hashes = {}
    try:
        with open(HASH_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                url, digest = line.split(';;')
                hashes[url] = digest
    except FileNotFoundError:
        pass
    return hashes


def _save_baseline_hash(url, digest):
    """
    Baseline Hash Writer
    -> Writes/updates one URL's known-good hash in site_hashes.txt
    """
    hashes = _load_baseline_hashes()
    hashes[url] = digest
    with open(HASH_FILE, 'w') as f:
        for u, d in hashes.items():
            f.write(f'{u};;{d}\n')


async def _fetch_hash(session, url):
    """
    Site Content Hasher
    -> Downloads a URL, following redirects
    -> Returns the sha256 hex digest of the response body
    """
    async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=15)) as response:
        body = await response.read()
    return hashlib.sha256(body).hexdigest()


async def _check_all_sites():
    """
    Site Check Runner
    -> Fetches and hashes every monitored URL
    -> Compares against its baseline, alerting once on a down/up transition
    -> Records a new baseline the first time a URL is ever checked
    """
    baseline_hashes = _load_baseline_hashes()
    channel = bot.get_channel(CATHID)

    async with aiohttp.ClientSession() as session:
        for url in SITE_MONITOR_URLS:
            try:
                digest = await _fetch_hash(session, url)
            except Exception as e:
                print(f'ERROR checking {url}: {e}')
                if not is_down[url]:
                    is_down[url] = True
                    if channel:
                        await channel.send(f'\U0001F534 {url} is down. Please investigate.')
                continue

            baseline = baseline_hashes.get(url)
            if baseline is None:
                # First time this URL has been checked: record it as the
                # known good hash instead of alerting.
                _save_baseline_hash(url, digest)
                continue

            if digest != baseline:
                if not is_down[url]:
                    is_down[url] = True
                    if channel:
                        await channel.send(f'\U0001F534 {url} is down. Please investigate.')
            else:
                if is_down[url]:
                    is_down[url] = False
                    if channel:
                        await channel.send(f'\U0001F7E2 {url} is back up.')


@tasks.loop(seconds=1200)
async def check_sites():
    """
    20-Minute Site Check Loop
    -> Wraps _check_all_sites() as a background task
    """
    await _check_all_sites()


@bot.command(name='checksites', help='Immediately checks the monitored sites (Council only)')
async def check_sites_now(ctx):
    """
    Bot Immediate Site Check Command
    -> Council-only: runs the same check the 20-minute loop runs, right now,
       then reports every site's current status regardless of whether it
       changed (unlike the loop, which only alerts on up/down transitions)
    """
    if not _is_council(ctx):
        return
    await ctx.send('Checking sites now...')
    await _check_all_sites()
    lines = []
    for url in SITE_MONITOR_URLS:
        if is_down[url]:
            lines.append(f'\U0001F534 {url} is down.')
        else:
            lines.append(f'\U0001F7E2 {url} is up.')
    await ctx.send('\n'.join(lines))


@bot.command(name='resethash', help='Clears the stored baseline hash for a monitored site (Council only)')
async def reset_hash(ctx, url):
    """
    Bot Reset Hash Command
    -> Council-only: clears the recorded baseline for a monitored URL so the
       next check records fresh content as the new known-good hash, instead
       of permanently alerting "down" after a deliberate content change
    """
    if not _is_council(ctx):
        return
    if url not in SITE_MONITOR_URLS:
        await ctx.send(f'{url} is not a monitored site. Monitored sites: {", ".join(SITE_MONITOR_URLS)}')
        return

    hashes = _load_baseline_hashes()
    hashes.pop(url, None)
    with open(HASH_FILE, 'w') as f:
        for u, d in hashes.items():
            f.write(f'{u};;{d}\n')
    is_down[url] = False

    await ctx.send(f'Baseline hash for {url} cleared. It will be re-recorded on the next check.')
