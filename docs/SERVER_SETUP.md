# Discord Server Setup

The bot does not create roles or channels for you - it looks them up by name (roles) or ID (channels) at runtime via `discord.utils.get(...)` / `bot.get_channel(...)`. These must already exist on the guild before the corresponding features will work.

## Required roles

| Role name | Used by | Purpose |
|---|---|---|
| `Council` | `!announce` (`announcements.py`), `!checksites` / `!resethash` (`site_monitor.py`) | Gates staff-only commands. The caller must have this role, checked via `discord.utils.get(ctx.guild.roles, name='Council')` / the `_is_council()` helper in `site_monitor.py`. |
| `Announcements` | `!sub` / `!unsub` (`roles.py`), `!announce` and the scheduled event reminders (`announcements.py`) | Pinged whenever an announcement goes out. Members opt in/out with `!sub`/`!unsub`. |
| `user` | `on_member_join` (`events.py`) | Auto-assigned to every new member when they join, alongside the welcome message. |

**Role name matching is case-sensitive where it matters for lookup, but self-service comparisons in `!role`/`!rmrole` are done lowercase.** Create the roles with exactly these names (`Council`, `Announcements`, `user`) to avoid lookup failures.

### `restricted_roles`

`config.py` defines:

```python
restricted_roles = ["Wizard Frog", "Council"]
```

Any role whose name (case-insensitively) matches an entry in this list cannot be self-assigned or self-removed via `!role`/`!rmrole` - `!roles` also excludes these from its listing (case-sensitive there). This is how `Council` (and the bot's own top role, `Wizard Frog`) stays out of members' hands even though `!role` will otherwise let anyone grab any named role on the server. If you rename the bot's own role or add other privileged roles, add them to this list.

Note `Announcements` and `user` are deliberately **not** in `restricted_roles` - `Announcements` is self-service by design (via `!sub`/`!unsub`, not `!role`), and `user` is assigned automatically on join rather than through role commands.

## Required channels

Channel IDs are read from `.env` as integers (see [`CONFIGURATION.md`](CONFIGURATION.md)) and passed to `bot.get_channel(...)`. The bot does not validate at startup that these IDs resolve to real channels it can see - a bad ID will just cause silent failures (e.g. `None.send(...)` exceptions) when that feature fires.

| Env var | Role in the bot | Used by |
|---|---|---|
| `WELCID` | Welcome channel | `on_member_join` posts the join gif + mention here; `_get_members()` posts catch-up welcome messages here on startup. |
| `ANNOID` | Announcements channel | `!announce` and the scheduled event reminder task post here. |
| `CATHID` | Restricted "mod channel" | `!announce` only works if invoked from this channel; `site_monitor` also posts its up/down alerts here (reusing the mod channel rather than a dedicated one). |

## Other prerequisites

- The bot needs the **"Manage Roles"** permission (to add/remove `user` and self-service roles) and its own role must sit **above** every role it needs to grant/revoke in the guild's role hierarchy, or `add_roles`/`remove_roles` calls will fail.
- The bot needs **Connect/Speak** permissions in whatever voice channels members expect to use `!join` in.
- Discord's intents: `bot_instance.py` requests `discord.Intents().all()`, so all privileged intents (members, presences, message content) must also be enabled for the bot application in the Discord Developer Portal, or `bot.run(TOKEN)` will fail at startup.
