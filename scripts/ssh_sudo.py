#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Manage and verify Mac 1Password -> Linux SSH/sudo without private-key fallback."""

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SOCKET = Path.home() / "Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
CACHE = ROOT / ".cache/ssh-sudo"


def run(argv, *, timeout=90, **kwargs):
    return subprocess.run(argv, text=True, capture_output=True, timeout=timeout, **kwargs)


def checked(argv, **kwargs):
    result = run(argv, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"Command failed: {argv[0]}")
    return result.stdout


def config():
    with (ROOT / "ssh-sudo/config.toml").open("rb") as stream:
        return tomllib.load(stream)


def agent_key(settings):
    environment = {**os.environ, "SSH_AUTH_SOCK": str(SOCKET)}
    keys = checked(["ssh-add", "-L"], env=environment)
    for key in keys.splitlines():
        fingerprint = checked(["ssh-keygen", "-lf", "-"], input=key + "\n")
        if fingerprint.split()[1] == settings["fingerprint"]:
            return key + "\n"
    raise RuntimeError(f"1Password does not offer {settings['fingerprint']}; unlock it and enable its SSH agent.")


def ssh_command(host, user, keyfile, *, forward=True):
    return [
        "ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=yes", "-o", "ControlPath=none",
        "-o", "IdentitiesOnly=yes", "-o", f'IdentityAgent="{SOCKET}"',
        "-i", str(keyfile), "-l", user, "-A" if forward else "-a", host,
    ]


def remote(command, script):
    return run([*command, "sh -s"], input="export LC_ALL=C\n" + script)


def require_success(result, label):
    if result.returncode:
        raise RuntimeError(f"{label}: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def test_host(command):
    forwarded = remote(command, 'test -S "$SSH_AUTH_SOCK" && ssh-add -l\n')
    require_success(forwarded, "agent forwarding")
    positive = remote(command, "sudo -k -n /usr/bin/id -u\n")
    if require_success(positive, "sudo through agent") != "0":
        raise RuntimeError("sudo did not run as root")
    negative = remote(command, "env -u SSH_AUTH_SOCK sudo -k -n /usr/bin/id -u\n")
    if negative.returncode == 0:
        raise RuntimeError("sudo succeeded WITHOUT the agent: a NOPASSWD rule or other bypass remains")
    if negative.returncode != 1 or ("password is required" not in negative.stderr and "authentication" not in negative.stderr.lower()):
        raise RuntimeError(f"Negative check was inconclusive: {negative.stderr.strip()}")
    # A distinct login with forwarding disabled must also be denied.
    no_forward = list(command)
    no_forward[no_forward.index("-A")] = "-a"
    negative = remote(no_forward, "sudo -k -n /usr/bin/id -u\n")
    if negative.returncode == 0:
        raise RuntimeError("sudo succeeded in a session without forwarding")
    if negative.returncode != 1 or ("password is required" not in negative.stderr and "authentication" not in negative.stderr.lower()):
        raise RuntimeError(f"Negative check was inconclusive: {negative.stderr.strip()}")
    return "agent-only SSH, forwarding, sudo uid=0; missing-agent and no-forwarding sudo denied"


def stage(command, keyfile):
    module = CACHE / "libpam_rssh.so"
    if not module.is_file():
        raise RuntimeError("Run just ssh-sudo-build first")
    digest = hashlib.sha256(module.read_bytes()).hexdigest()
    path = require_success(remote(command, "umask 077; mktemp -d /tmp/ssh-sudo.XXXXXXXX\n"), "staging directory")
    # Transfer through the same strictly agent-only transport, without scp configuration drift.
    for source, name in ((module, "libpam_rssh.so"), (keyfile, "admin.pub"),
                         (ROOT / "ssh-sudo/install.py", "install.py")):
        result = subprocess.run([*command, f"cat > {shlex.quote(path + '/' + name)}"],
                                input=source.read_bytes(), capture_output=True, timeout=90)
        if result.returncode:
            raise RuntimeError(f"Could not stage {name}")
    print(f"Staged module SHA256 {digest}")
    print(f'On the host, run: sudo python3 {path}/install.py install --stage {path} --sha256 {digest} --socket "$SSH_AUTH_SOCK"')
    return path, digest


def enroll(host, user, key):
    script = '''import os, pathlib, sys
key = sys.stdin.read().strip()
directory = pathlib.Path.home() / ".ssh"
path = directory / "authorized_keys"
if directory.is_symlink() or path.is_symlink():
    raise SystemExit("Refusing symlink in SSH authorization path")
directory.mkdir(mode=0o700, exist_ok=True)
original = path.read_text() if path.exists() else ""
if not any(line.split()[:2] == key.split()[:2] for line in original.splitlines()):
    with path.open("a") as stream:
        stream.write(("\\n" if original and not original.endswith("\\n") else "") + key + "\\n")
    os.chmod(path, 0o600)
    print("Enrolled 1Password public key; existing keys retained")
else:
    print("1Password public key already enrolled")
'''
    # Explicit bootstrap only. Doctor/test/install never use this recovery-key transport.
    command = ["ssh", "-F", "/dev/null", "-l", user,
               "-i", str(Path.home() / ".ssh/id_ed25519"),
               "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none", "-o", "BatchMode=yes",
               "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=yes", host,
               "python3 -c " + shlex.quote(script)]
    print(checked(command, input=key))


def configure_mac(key):
    directory = Path.home() / ".ssh"
    path = directory / "config"
    public = directory / "1password-admin.pub"
    if path.is_symlink() or public.is_symlink():
        raise RuntimeError("Refusing to overwrite a symlink in Mac SSH configuration")
    original = path.read_text()
    old = 'Host betty\n\tForwardAgent yes\n\nHost betty gertrude\n\tUser wcygan\n\tIdentityFile ~/.ssh/id_ed25519\n'
    new = ('Host betty gertrude\n\tUser wcygan\n'
           '\tIdentityFile ~/.ssh/1password-admin.pub\n\tIdentitiesOnly yes\n\tForwardAgent yes\n')
    if original.endswith(new):
        if public.read_text() != key:
            raise RuntimeError("Public identity differs: perform an explicit key rotation")
        print("Mac SSH configuration already matches")
        return
    if not original.endswith(old):
        raise RuntimeError("Mac SSH config differs from the inspected baseline; review it before modifying")
    if public.exists() and public.read_text() != key:
        raise RuntimeError("Existing 1password-admin.pub differs; refusing to overwrite")
    backup = directory / ("config.before-ssh-sudo-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.write_text(original)
    backup.chmod(0o600)
    public.write_text(key)
    public.chmod(0o644)
    path.write_text(original[:-len(old)] + new)
    path.chmod(0o600)
    print(f"Configured public-only identity and forwarding for Betty/Gertrude; backup: {backup}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "test", "enroll", "configure-mac", "stage", "install"])
    parser.add_argument("hosts", nargs="*")
    args = parser.parse_args()
    settings = config()
    if settings["user"] != "wcygan":
        parser.error("The remote installer currently supports only wcygan")
    hosts = args.hosts or settings["hosts"]
    if any(host not in settings["hosts"] for host in hosts):
        parser.error("Host must be in ssh-sudo/config.toml")
    failures = 0
    try:
        key = agent_key(settings)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"FAIL Mac 1Password agent: {error}", file=sys.stderr)
        return 1
    print(f"PASS Mac 1Password agent: {settings['fingerprint']}")
    if args.action == "configure-mac":
        configure_mac(key)
        return 0
    with tempfile.TemporaryDirectory(prefix="ssh-sudo-") as temporary:
        keyfile = Path(temporary) / "admin.pub"
        keyfile.write_text(key)
        for host in hosts:
            command = ssh_command(host, settings["user"], keyfile)
            try:
                if args.action == "enroll":
                    enroll(host, settings["user"], key)
                elif args.action == "doctor":
                    script = '''set -eu
. /etc/os-release
printf 'os=%s arch=%s user=%s\\n' "$PRETTY_NAME" "$(uname -m)" "$(id -un)"
test -S "$SSH_AUTH_SOCK"
ssh-add -l
cat /etc/pam.d/sudo
sudo -k -n -l
'''
                    print(require_success(remote(command, script), host))
                elif args.action == "test":
                    print(f"PASS {host}: {test_host(command)}")
                else:
                    path, digest = stage(command, keyfile)
                    if args.action == "install":
                        install = f'sudo python3 {path}/install.py install --stage {path} --sha256 {digest} --socket "$SSH_AUTH_SOCK"'
                        # stdin remains attached to the user's terminal for a bootstrap password.
                        result = subprocess.run([*command[:-1], "-t", host, install], timeout=300)
                        if result.returncode:
                            raise RuntimeError("Installation failed; inspect host backup before retrying")
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                failures += 1
                print(f"FAIL {host}: {error}", file=sys.stderr)
    return int(failures != 0)


if __name__ == "__main__":
    sys.exit(main())
