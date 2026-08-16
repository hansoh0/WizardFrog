# Command Reference

23 commands total, grouped by feature module. All commands use the `!` prefix. Quoted arguments (`"[role]"`, `"[suggestion]"`) need actual quotes when they contain spaces, since discord.py splits on whitespace.

## Misc (`py_components/fun.py`)

| Command | Description |
|---|---|
| `!help` | Prints the full command list, grouped by category. |
| `!hackers` | Sends the "Mess with the best... Hack the planet!" quote from *Hackers* (1995). |
| `!trolldetected` | Sends the "TROLL DETECTED / BLAST 'EM" bit. |
| `!beep` | Replies "boop". |
| `!thanks` | Sends a random line from the `quips` flavor-text list in `config.py` (empty by default - populate it to use this command). |

## Roles (`py_components/roles.py`)

| Command | Description |
|---|---|
| `!roles` | Lists all assignable (non-restricted, non-`@everyone`) roles on the server. |
| `!role "[role]"` | Assigns the named role to the caller, unless it's in `restricted_roles`. |
| `!rmrole "[role]"` | Removes the named role from the caller, unless it's restricted. |
| `!sub` | Adds the `Announcements` role to the caller. |
| `!unsub` | Removes the `Announcements` role from the caller. |

## Jukebox (`py_components/music.py`)

| Command | Description |
|---|---|
| `!join` | Bot joins the caller's voice channel. Fails if the bot is already in a VC or the caller isn't in one. |
| `!leave` | Bot leaves the VC and clears the queue. Only the user who ran `!join` can do this. |
| `!q [youtube link]` | Downloads a YouTube link via yt-dlp and adds it to the queue, if it's under 8 minutes and the queue (max 10) isn't full. |
| `!lsq` | Lists the titles currently in the queue. |
| `!start` | Plays through the queue one song at a time. |
| `!stop` | Stops the current song and removes it from the queue. Only the user who queued that song can do this. |

## Announcements (`py_components/announcements.py`)

| Command | Description |
|---|---|
| `!announce "[text]"` | Posts an announcement (pinging `@Announcements`) to the announcements channel. Restricted: caller must have the `Council` role and must run it from the mod channel (`CATHID`). Rejects text containing characters outside a whitelist. |

Scheduled event reminders (one week / three days / one day before a Discord server event) are posted automatically by the `announce_events` background task - there's no user-facing command for this.

## Minecraft (`py_components/minecraft.py`)

| Command | Description |
|---|---|
| `!mcstatus` | Queries `MC_SERVER_ADDRESS` (a Java Edition server) and reports whether it's up/down and who's currently in-game. |

## Site monitor (`py_components/site_monitor.py`)

| Command | Description |
|---|---|
| `!checksites` | Council-only. Immediately checks every monitored URL and reports each one's current status (up/down), regardless of whether it changed since the last check. |
| `!resethash [url]` | Council-only. Clears the stored baseline hash for one monitored URL, so the next check records its current content as the new known-good baseline instead of comparing against stale content. |

## Submissions (`py_components/submissions.py`)

| Command | Description |
|---|---|
| `!suggest "[suggestion]"` | Writes a suggestion to `SUBMIT/suggestions.txt`. Rejects text outside an allowed-character whitelist. |
| `!submit [category] [text]` | Writes a gif/pic/song/movie submission (with a jump link to the message) to that category's submission file. Valid categories: `gif`, `pic`, `song`, `movie`. |
| `!random [category]` | Sends a random file from `GIFS/` or `PICS/`. `fact`, `movie`, and `song` are accepted as categories by the help text but aren't implemented yet - the bot replies that the category isn't available. |

## Notes

- `!help`'s in-bot text is a hand-maintained summary and may drift slightly from this table over time (e.g. it doesn't currently list `!announce`, `!checksites`, or `!resethash`, since those are staff-only). This document and the module docstrings in the code are the authoritative reference.
- Commands gated by role or channel (`!announce`, `!checksites`, `!resethash`) silently no-op for unauthorized callers rather than sending a permission-denied message - see [`SERVER_SETUP.md`](SERVER_SETUP.md) for what "authorized" means for each.
