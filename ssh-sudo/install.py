#!/usr/bin/env python3
"""Root-side, transactional sudo/PAM installer. Never changes SSH login policy."""

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

USER = "wcygan"
BACKUPS = Path("/var/backups/ssh-sudo")
KEY = Path("/etc/security/ssh-sudo/wcygan.keys")
SUDOERS = Path("/etc/sudoers.d/90-ssh-sudo")
PAM = Path("/etc/pam.d/sudo")
MARKER = "# Managed by betty/ssh-sudo/install.py"


def pam_content(original, module):
    rule = f"auth sufficient {module} auth_key_file=/etc/security/ssh-sudo/${{user}}.keys"
    if MARKER in original:
        if rule not in original:
            raise ValueError("Existing managed PAM rule differs; inspect before changing it")
        return original
    if "pam_rssh" in original or "pam_ssh_agent" in original:
        raise ValueError("Unmanaged SSH-agent PAM configuration exists")
    return MARKER + "\n" + rule + "\n" + original


def remove_known_bypass(content):
    lines = content.splitlines(keepends=True)
    return "".join(line for line in lines if line.strip() != "wcygan ALL=(ALL) NOPASSWD: ALL")


def write(path, data, mode=0o644):
    if path.is_symlink():
        raise ValueError(f"Refusing symlink: {path}")
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.chown(temporary, 0, 0)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def restore(backup):
    manifest = json.loads((backup / "manifest.json").read_text())
    # Root-owned backup preserves original mode/owner, including absent files.
    for entry in reversed(manifest):
        path = Path(entry["path"])
        if entry["exists"]:
            write(path, (backup / entry["name"]).read_bytes(), entry["mode"])
            os.chown(path, entry["uid"], entry["gid"])
        else:
            path.unlink(missing_ok=True)
        if shutil.which("restorecon") and path.exists():
            subprocess.run(["restorecon", str(path)], check=True)
    subprocess.run(["visudo", "-cf", "/etc/sudoers"], check=True)


def install(args):
    release = Path("/etc/os-release").read_text()
    fedora = 'ID=fedora-asahi-remix' in release and 'VERSION_ID=44' in release
    debian = 'ID=debian' in release and 'VERSION_ID="12"' in release
    if platform.machine() != "aarch64" or not (fedora or debian):
        raise ValueError("Only the inspected Fedora Asahi 44 and Debian 12 ARM64 hosts are supported")
    module = Path("/usr/lib64/security/libpam_rssh.so" if fedora else
                  "/usr/lib/aarch64-linux-gnu/security/libpam_rssh.so")
    binary = (args.stage / "libpam_rssh.so").read_bytes()
    if hashlib.sha256(binary).hexdigest() != args.sha256:
        raise ValueError("Staged module SHA256 mismatch")
    key = (args.stage / "admin.pub").read_bytes()
    subprocess.run(["ssh-keygen", "-lf", str(args.stage / "admin.pub")], check=True)
    # Load the verified bytes from a root-only directory, not the mutable staging path.
    with tempfile.TemporaryDirectory(prefix="ssh-sudo-verified-", dir="/root") as temporary:
        verified = Path(temporary) / "libpam_rssh.so"
        verified.write_bytes(binary)
        ctypes.CDLL(str(verified))
    pam = pam_content(PAM.read_text(), module).encode()
    policy = (MARKER + '\nDefaults:wcygan env_keep += "SSH_AUTH_SOCK"\n'
              'Defaults:wcygan noninteractive_auth\n').encode()
    desired = {module: binary, KEY: key, SUDOERS: policy, PAM: pam}
    # Only these two observed Raspberry Pi bypass rules are migrated.
    for path in (Path("/etc/sudoers"), Path("/etc/sudoers.d/010_pi-nopasswd")):
        if path.exists():
            original = path.read_text()
            replacement = remove_known_bypass(original)
            if replacement != original:
                desired[path] = replacement.encode()
    for path in desired:
        if path.is_symlink():
            raise ValueError(f"Refusing symlink: {path}")
    changed = {path: data for path, data in desired.items()
               if not path.exists() or path.read_bytes() != data}
    if not changed:
        print("Configuration already matches; running behavior checks")
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = BACKUPS / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup.mkdir(mode=0o700)
    manifest = []
    for index, path in enumerate(changed):
        entry = {"path": str(path), "exists": path.exists(), "name": str(index)}
        if path.exists():
            info = path.stat()
            entry.update(mode=info.st_mode & 0o777, uid=info.st_uid, gid=info.st_gid)
            shutil.copyfile(path, backup / str(index))
        manifest.append(entry)
    (backup / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Rollback: sudo python3 {args.stage}/install.py rollback --backup {backup}", flush=True)
    try:
        for path, data in changed.items():
            write(path, data, 0o440 if path == SUDOERS or path.name == "sudoers" else 0o644)
            if shutil.which("restorecon"):
                subprocess.run(["restorecon", str(path)], check=True)
        subprocess.run(["visudo", "-cf", "/etc/sudoers"], check=True)
        base = ["runuser", "-u", USER, "--", "env"]
        positive = subprocess.run([*base, f"SSH_AUTH_SOCK={args.socket}", "sudo", "-k", "-n",
                                   "/usr/bin/id", "-u"], capture_output=True, text=True, timeout=90)
        if positive.returncode or positive.stdout.strip() != "0":
            raise RuntimeError(f"Agent sudo failed: {positive.stderr.strip()}")
        negative = subprocess.run([*base, "-u", "SSH_AUTH_SOCK", "sudo", "-k", "-n",
                                   "/usr/bin/id", "-u"], capture_output=True, text=True, timeout=15)
        if negative.returncode == 0:
            raise RuntimeError("Sudo bypass remains: no-agent sudo still succeeds")
        print("PASS: forwarded-agent sudo succeeds; no-agent sudo denied", flush=True)
    except BaseException:
        restore(backup)
        print("Restored original configuration after failed verification", flush=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "rollback"])
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--sha256")
    parser.add_argument("--socket")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run as root through sudo")
    if args.action == "rollback":
        if not args.backup or args.backup.parent != BACKUPS:
            parser.error("--backup must name a directory directly under /var/backups/ssh-sudo")
        restore(args.backup)
    else:
        if not args.stage or not args.sha256 or not args.socket:
            parser.error("install requires --stage, --sha256 and --socket")
        install(args)


if __name__ == "__main__":
    main()
