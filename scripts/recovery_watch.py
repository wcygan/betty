#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Time Betty's unattended recovery stages from the MacBook.

Start this, then cut Betty's power or restart it, and do not touch Betty.
It waits for Betty to drop off, then records when each stage returns:
SSH as rat over Tailscale, automatic login, the Tailscale app, and the Rex
server answering. See docs/macos-unattended-recovery.md.
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from datetime import datetime


class Watcher:
    def __init__(self, ssh_host: str, rex_host: str, lan_host: str | None) -> None:
        self.ssh_host = ssh_host
        self.rex_host = rex_host
        self.lan_host = lan_host
        self.seen: dict[str, float] = {}

    def log(self, stage: str, detail: str) -> None:
        if stage in self.seen:
            return
        self.seen[stage] = time.monotonic()
        elapsed = self.seen[stage] - self.seen.get("down", self.seen[stage])
        stamp = datetime.now().strftime("%H:%M:%S")
        print(f"{stamp}  +{elapsed:5.0f}s  {stage:<14} {detail}", flush=True)

    def lan_up(self) -> bool:
        if self.lan_host is None:
            return False
        try:
            with socket.create_connection((self.lan_host, 22), timeout=3):
                return True
        except OSError:
            return False

    def ssh(self, command: str) -> str | None:
        try:
            result = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", self.ssh_host, command],
                capture_output=True, text=True, timeout=20,
            )
        except subprocess.TimeoutExpired:
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    def rex_up(self) -> bool:
        result = subprocess.run(
            ["rex", "--timeout", "8s", "--autostart=false", "-S", self.rex_host, "ls"],
            capture_output=True, text=True,
        )
        return result.returncode == 0

    def reachable(self) -> bool:
        if self.lan_host is not None:
            return self.lan_up()
        return self.ssh("true") is not None

    def wait_for_down(self, deadline: float) -> bool:
        while time.monotonic() < deadline:
            if not self.reachable():
                self.log("down", "Betty stopped answering")
                return True
            time.sleep(2)
        return False

    def wait_for_recovery(self, deadline: float, interval: float) -> bool:
        required = {"tailscale-ssh", "autologin", "tailscale-app", "rex-server"}
        while time.monotonic() < deadline:
            if self.lan_up():
                self.log("lan-ssh-port", "LAN port 22 answers (booted to network)")
            out = self.ssh("stat -f %Su /dev/console; pgrep -lf 'Tailscale|IPNExtension' | head -3")
            if out is not None:
                self.log("tailscale-ssh", "SSH as rat over Tailscale works")
                lines = out.splitlines()
                if lines and lines[0] == "rat":
                    self.log("autologin", "console user is rat")
                if any("Tailscale" in line or "IPNExtension" in line for line in lines[1:]):
                    self.log("tailscale-app", "Tailscale app running")
                if self.rex_up():
                    self.log("rex-server", f"{self.rex_host} answers rex ls")
            if required <= self.seen.keys():
                return True
            time.sleep(interval)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ssh-host", default="betty", help="SSH alias for rat on Betty")
    parser.add_argument("--rex-host", default="betty", help="rex host label or address")
    parser.add_argument("--lan-host", help="Betty's wired LAN address, to time the network boot stage")
    parser.add_argument("--interval", type=float, default=5, help="seconds between checks")
    parser.add_argument("--minutes", type=float, default=45, help="give up after this long")
    args = parser.parse_args()

    watcher = Watcher(args.ssh_host, args.rex_host, args.lan_host)
    deadline = time.monotonic() + args.minutes * 60
    print("watching; cut Betty's power or restart it now, then leave it alone", flush=True)
    if not watcher.wait_for_down(deadline):
        print("Betty never went offline", flush=True)
        return 1
    if watcher.wait_for_recovery(deadline, args.interval):
        uptime = watcher.ssh("uptime") or "?"
        print(f"recovered. {uptime}", flush=True)
        return 0
    print(f"timed out; stages seen: {', '.join(sorted(watcher.seen))}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
