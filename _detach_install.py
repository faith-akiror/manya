"""Run a dependency install fully detached from the invoking shell.

Usage (from the repo root):
    python _detach_install.py

Spawns `pip install -r requirements.txt` as a detached Windows process
(survives the caller shell being killed) and prints the child PID.
Output is written to install.log / install_err.log.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "install.log")
ERR = os.path.join(ROOT, "install_err.log")

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000

with open(LOG, "wb") as out, open(ERR, "wb") as eout:
    proc = subprocess.Popen(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=eout,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
        close_fds=True,
    )
print(proc.pid)
