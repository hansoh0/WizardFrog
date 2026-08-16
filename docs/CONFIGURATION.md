# Configuration

The bot reads its configuration from environment variables, loaded from a `.env` file in `py_components/` via `python-dotenv` (`config.py` calls `load_dotenv()` at import time). Create `py_components/.env` before running the bot - it is git-ignored and never committed.

## Environment variables

| Variable | Type | Used for | Breaks without it |
|---|---|---|---|
| `TOKEN` | string | The Discord bot token, passed to `bot.run(TOKEN)` in `main.py`. | The bot can't log in at all. |
| `SERVID` | int (Discord guild/snowflake ID) | The main server the bot operates on - used to fetch the guild via `bot.get_guild(SERVID)` for scheduled-event syncing (`announcements.py`) and the member-join backfill (`events.py`). | Scheduled event reminders and the join-backfill on startup. |
| `WELCID` | int (channel ID) | Welcome channel - see [`SERVER_SETUP.md`](SERVER_SETUP.md). | New-member welcome messages, join-backfill messages. |
| `ANNOID` | int (channel ID) | Announcements channel - see [`SERVER_SETUP.md`](SERVER_SETUP.md). | `!announce` and scheduled event reminders have nowhere to post. |
| `CATHID` | int (channel ID) | Restricted "mod channel" - see [`SERVER_SETUP.md`](SERVER_SETUP.md). | `!announce` can't be invoked from anywhere (it checks `ctx.channel.id != CATHID`); site monitor alerts have nowhere to post. |
| `ROOT` | filesystem path | Root of the persistent data directory (loaded into `config.py` as `WPATH`). Must already exist - `config.py` raises at startup and the bot never comes up if it doesn't. All file-backed features read/write under this path. | Everything - the bot refuses to start at all if `ROOT` is unset or doesn't exist; jukebox downloads, submissions, logs, event storage, and site-monitor hashes all live under it. |
| `MC_SERVER_ADDRESS` | string, `host:port` | Address of the Minecraft Java server checked by `!mcstatus`. | `!mcstatus` (fails/errors without a valid address). |
| `SITE_ONE`, `SITE_TWO`, `SITE_THREE` | URL strings | The three websites monitored by `site_monitor.py`'s background loop and `!checksites`/`!resethash`. Collected into `SITE_MONITOR_URLS` (fixed at 3 entries - `config.py` doesn't support a variable-length list). | Site monitor has nothing to check (empty/`None` URLs will error on fetch). |

`config.py` also defines two constants that are **not** environment-driven:

- `quips` - a flavor-text list `!thanks` picks a random line from. Starts empty (`quips = []`); populate it in code to enable `!thanks` output.
- `restricted_roles` - `["Wizard Frog", "Council"]`. See [`SERVER_SETUP.md`](SERVER_SETUP.md) for what this gates.

## Required `store/` directory layout

`WPATH` (the `ROOT` env var) points at a directory laid out like this. `ROOT` itself must already exist when the bot starts - it's the deployment's job to create it (e.g. the Dockerfile creates `/home/wizardfrog/app` for the Docker deployment); `config.py` deliberately refuses to create `ROOT` itself and raises a clear error at startup if it's missing, rather than silently creating a directory tree wherever a misconfigured `ROOT` happens to point. Once `ROOT` exists, `config.py` does create the five subdirectories below under it on startup (`os.makedirs(..., exist_ok=True)`) if they're not already there:

```
<ROOT>/
├── GIFS/            # !random gif pulls from here (needs at least one file to work)
├── JUKE/             # yt-dlp downloads land here while queued/playing; cleaned up on song end and bot shutdown
├── LOGS/
│   ├── userlist.txt  # one Discord user ID per line; tracks who's already gotten a welcome message
│   └── botLog.txt    # created on demand by submissions.py's error-fallback path
├── PICS/             # !random pic pulls from here
├── SUBMIT/
│   ├── suggestions.txt   # created on demand by !suggest
│   ├── gifSub.txt        # created on demand by !submit gif
│   ├── picSub.txt        # created on demand by !submit pic
│   ├── songSub.txt       # created on demand by !submit song
│   └── movieSub.txt      # created on demand by !submit movie
├── schevents.txt      # scheduled-event reminder state, written/read by announcements.py
└── site_hashes.txt    # per-URL baseline content hashes, written/read by site_monitor.py
```

`GIFS/`, `JUKE/`, `LOGS/`, `PICS/`, and `SUBMIT/` are auto-created empty on startup, as described above. The `.txt` files inside `SUBMIT/` and the top-level `schevents.txt` / `site_hashes.txt` are created automatically the first time something is written to them (`open(..., 'a')` / `open(..., 'w')`). `GIFS/` and `PICS/` still need at least one actual gif/pic file dropped in manually for `!random gif`/`!random pic` to have something to serve - only the directories themselves are created automatically, not their contents.

If deploying with Docker, this same layout should be mounted as a volume so it persists across container restarts/rebuilds - see the Docker section of the root [`README.md`](../README.md).
