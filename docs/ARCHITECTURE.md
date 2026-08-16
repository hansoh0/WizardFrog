# Architecture

The bot was refactored from a single ~1000-line file into a multi-file package under `py_components/`. This doc covers the module layout, the naming convention used throughout, and how to add a new feature module.

## Module layout

| File | Role |
|---|---|
| `main.py` | Entry point. Imports `config` and `bot_instance` for `TOKEN`/`bot`, imports every feature module (so their commands/events register on `bot` as a side effect of import), then calls `bot.run(TOKEN)`. Cleans up leftover jukebox files on exit via `music.cleanup_end()`. |
| `bot_instance.py` | Defines the single shared `commands.Bot` instance (`bot`) that every feature module imports and registers commands/events against. Also defines `intents` (all intents enabled) and an unused `stop_event` carried over from the original single-file bot. |
| `config.py` | Loads `.env` via `python-dotenv` and exposes environment-driven constants (`TOKEN`, `SERVID`, `WELCID`, `ANNOID`, `CATHID`, `WPATH`, `MC_SERVER_ADDRESS`, `SITE_MONITOR_URLS`) plus two hardcoded constants (`quips`, `restricted_roles`). See [`CONFIGURATION.md`](CONFIGURATION.md). |
| `music.py` | Jukebox: VC join/leave, YouTube download via yt-dlp, queue playback. |
| `roles.py` | Role self-service (`!role`/`!rmrole`/`!roles`) and announcement subscription (`!sub`/`!unsub`). |
| `announcements.py` | Manual announcements (`!announce`) plus the scheduled-event sync/reminder system (`announce_events` task) and a bot-status rotator (`change_bot_status` task). |
| `submissions.py` | Suggestion box (`!suggest`) and community submissions (`!submit`/`!random`). |
| `fun.py` | Misc/flavor commands and `!help`. |
| `events.py` | Bot lifecycle: `on_ready` (starts background tasks + runs member backfill), `on_error`, `on_member_join`, `on_voice_state_update`, and the `_get_members()` backfill helper. |
| `minecraft.py` | `!mcstatus`. |
| `site_monitor.py` | Website content-integrity monitor: hourly-loop hash comparison, `!checksites`, `!resethash`. |

Every module has a module-level docstring that catalogs every function in it with a one-line summary - read those first when orienting in a file. Most individual functions also carry an inline docstring in a `"""Name\n-> bullet\n-> bullet"""` style describing behavior and edge cases; those docstrings are kept accurate and are the fastest way to understand what a function does without re-deriving it from the implementation.

## Naming convention: leading underscore = internal helper

Across every module, a function name with a **leading underscore** (e.g. `_is_council`, `_get_members`, `_update_events`, `_convert_time`) is a private helper - it's only ever called from within its own file and isn't part of that module's public surface.

A function **without** a leading underscore is part of the module's public surface: it's either

- a `@bot.command` (a slash-prefixed Discord command),
- a `@bot.event` listener (registered in `events.py`), or
- a `@tasks.loop` background task that gets `.start()`ed from another module (e.g. `events.py`'s `on_ready` starts `announcements.announce_events`, `announcements.change_bot_status`, and `site_monitor.check_sites`).

When adding new code, follow this convention: prefix a helper with `_` the moment it's not meant to be imported/called from outside its file, and leave the prefix off anything another module (most often `events.py`, for task startup) needs to reach.

## Cross-module dependencies

Every feature module imports `bot` from `bot_instance.py` to register its commands/events. Beyond that, most modules are self-contained. The two intentional cross-module couplings are:

- `events.py` imports `announcements` and `site_monitor` (to call `.start()` on their background tasks from `on_ready`) and imports `queue` from `music` (to clear the jukebox queue on `on_voice_state_update` when a voice channel empties out).
- `main.py` imports `music` (for `cleanup_end()` on shutdown) and every other feature module purely for their import-time side effect of registering commands/events on `bot`.

Avoid introducing new cross-module imports beyond what's needed to register with `bot` or wire up lifecycle/task startup in `events.py` - keeping feature modules independent of each other is what makes this layout easier to maintain than the original single file.

## Adding a new feature module

1. Create `py_components/<feature>.py`.
2. At the top, `from bot_instance import bot` (and `from config import ...` for whatever constants you need).
3. Add a module-level docstring cataloging every function, one line each, matching the style of the existing modules.
4. Define your commands with `@bot.command(name=..., help=...)` and/or background tasks with `@tasks.loop(seconds=...)`. Give internal-only helpers a leading underscore; leave it off anything `events.py` needs to start or another module needs to call.
5. In `main.py`, add `import <feature>` alongside the existing feature imports - this is what actually registers your commands/events on `bot`. Nothing else needs to change; `main.py` doesn't call anything from the module directly except (for `music`) its shutdown cleanup.
6. If your module starts a `@tasks.loop` task, wire its `.start()` call into `events.py`'s `on_ready`, the same way `announce_events`, `change_bot_status`, and `check_sites` are started today.
7. If your feature needs persistent storage, put it under a new subdirectory of `WPATH` and document it in [`CONFIGURATION.md`](CONFIGURATION.md).
