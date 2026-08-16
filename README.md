
# Wizard Frog

Wizard Frog is a new-and-improved not-so state-of-the-art discord bot featuring role management, a VC Jukebox, event scheduling & reminders, automated & manual announcments, a mincraft server status checker (java), a website monitor, and submission & suggestion capabilities.

## Features

- **Role self-service** - members grant/revoke their own roles and toggle announcement pings without needing a moderator.
- **VC Jukebox** - queue and play YouTube audio in a voice channel, one song at a time.
- **Announcements** - Council members can push a manual announcement, and the bot automatically reminds the server about upcoming scheduled Discord events (one week / three days / one day out).
- **Minecraft server status** - checks a configured Java server and reports who's online.
- **Website content-integrity monitor** - periodically hashes a set of URLs and posts an alert if the content changes or the site goes down, plus on-demand checks.
- **Suggestion box & community submissions** - members can suggest features or submit gifs/pics/songs/movies for the council to review, and pull a random item back out.
- **Misc/fun commands** - `!help`, quotes, and small flavor commands.

Full behavior details for every command live in `py_components/*.py` - every function has a docstring, and each module's docstring is a one-line catalog of everything in it.

## Installation

Install requirements with pip

```
pip install -r py_components/requirements.txt
```

The bot logs via plain `print()` to stdout/stderr - under `systemctl`/`journalctl` this shows up automatically (systemd captures a unit's stdout/stderr by default), and under Docker it's captured by the container's log driver (`docker logs`/`docker compose logs`). No extra logging setup or system packages are needed either way.

## Configuration

The bot loads its configuration from a `.env` file in `py_components/` (via `python-dotenv`). See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) for the full list of environment variables, what each one controls, and the `store/` directory layout the bot expects `ROOT` to point at.

## Discord server setup

The bot expects specific roles and channels to already exist on the guild - it does not create them. See [`docs/SERVER_SETUP.md`](docs/SERVER_SETUP.md) for the full list (roles: `Council`, `Announcements`, `user`; channels: welcome, announcements, mod/restricted).

## Commands

23 commands across 8 feature areas. See [`docs/COMMANDS.md`](docs/COMMANDS.md) for the full reference, or run `!help` in Discord for the in-bot summary. Quick index:

| Area | Commands |
|---|---|
| Misc | `!help`, `!hackers`, `!trolldetected`, `!beep`, `!thanks` |
| Roles | `!roles`, `!role`, `!rmrole`, `!sub`, `!unsub` |
| Jukebox | `!join`, `!leave`, `!q`, `!lsq`, `!start`, `!stop` |
| Announcements | `!announce` |
| Minecraft | `!mcstatus` |
| Site monitor | `!checksites`, `!resethash` |
| Submissions | `!suggest`, `!submit`, `!random` |

## Architecture

The bot lives in `py_components/` as a multi-file package. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full breakdown, the naming convention used throughout the codebase, and how to wire in a new feature module.

## Setup

The bot is best set up as a service on a container
```
sudo vi /etc/systemd/system/WizardFrog.service
```
```
[Unit]
Description=Wizard Frog Discord Bot
After=networking.target

[Service]
User=rtwo
ExecStart=/usr/bin/python3 /home/WizardFrog/app/py_components/main.py

[Install]
WantedBy=multi-user.target
```
Reload daemons, enable WizardFrog to start on boot
```
sudo systemctl daemon-reload
sudo systemctl enable WizardFrog.service
sudo systemctl start WizardFrog.service
```

### Docker

The bot can also be run in Docker; see `docker-compose.yml` / `Dockerfile` at the repo root for the containerized deployment. Whichever way you run it, the container needs the same `py_components/.env` file and a mounted `store/` volume (with the subdirectories described in [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)) so submissions, jukebox downloads, logs, and monitor state persist across restarts.
