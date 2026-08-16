"""
Environment configuration and bot wide constants, loaded from .env.

TOKEN:
Discord bot token

SERVID:
Main Discord server (guild) ID

WELCID:
Welcome channel ID, used for member join messages

ANNOID:
Announcements channel ID, where !announce posts

CATHID:
Restricted "mod channel" ID; also where site_monitor posts up/down alerts

WPATH:
Root data directory - JUKE, SUBMIT, LOGS, GIFS, PICS, schevents.txt, and
site_hashes.txt all live under here

MC_SERVER_ADDRESS:
host:port of the Minecraft server checked by !mcstatus

SITE_MONITOR_URLS:
The websites checked by site_monitor's scheduled loop and
!checksites / !resethash commands

quips:
Flavor-text lines !thanks picks from at random

restricted_roles:
Role names that can't be self assigned/removed via !role or !rmrole
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ENV Globals
TOKEN = os.getenv("TOKEN")
SERVID = int(os.getenv("SERVID"))
WELCID = int(os.getenv("WELCID"))
ANNOID = int(os.getenv("ANNOID"))
CATHID = int(os.getenv("CATHID"))
WPATH = os.getenv("ROOT")

# ROOT itself is the deployment's responsibility to create (e.g. the
# Dockerfile), not the app's -- if it's missing that's a deployment/config
# mistake and should fail loudly here rather than have the app silently
# create a directory tree wherever ROOT happens to point.
if not WPATH or not os.path.isdir(WPATH):
    raise RuntimeError(
        f"ROOT ({WPATH!r}) is not set to an existing directory. It must be "
        "created by the deployment (e.g. the Dockerfile) before the bot "
        "starts."
    )

# Create subdirectories
for _subdir in ("GIFS", "JUKE", "LOGS", "PICS", "SUBMIT"):
    os.makedirs(os.path.join(WPATH, _subdir), exist_ok=True)

MC_SERVER_ADDRESS = os.getenv("MC_SERVER_ADDRESS")
SITE_MONITOR_URLS = [
    os.getenv("SITE_ONE"),
    os.getenv("SITE_TWO"),
    os.getenv("SITE_THREE"),
]

# Bot Globals
quips = [f"SHADOW WIZARD MONEY GANG, WE LOVE CASTING SPELLS \U0001F4AF",
"SPONSORED BY THE SHADOW GOVERNMENT. \U0001F608",
"\U0001F919 MAGIC POWERS! MAGIC POWERS FOR ABSOLUTELY FREE! \U0001F919",
"WIZARD POWERS.",
"CASTIN\' SPELLS.",
"WIZ BIZ, KID."]

restricted_roles = ["Wizard Frog", "Council"]
