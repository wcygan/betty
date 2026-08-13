#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the bounded Mac-to-Betty graphical desktop workflow."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass


DEFAULT_HOST = os.environ.get("BETTY_HOST", "betty")
DEFAULT_RDP_HOST = os.environ.get("BETTY_RDP_HOST", DEFAULT_HOST)
DEFAULT_RDP_PORT = int(os.environ.get("BETTY_RDP_PORT", "3389"))
RUSTDESK_RELEASE_API = "https://api.github.com/repos/rustdesk/rustdesk/releases/latest"
SSH_OPTIONS = (
    "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o",
    "IdentityAgent=none", "-o", "ConnectTimeout=10",
)
HOSTNAME_PATTERN = re.compile(
    r"(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z"
)
RUSTDESK_ASSET_PATTERN = re.compile(r"rustdesk-[A-Za-z0-9._-]+\.aarch64\.rpm\Z")
SHA256_PATTERN = re.compile(r"sha256:([0-9a-f]{64})\Z")


class HarnessError(RuntimeError):
    """A bounded workflow failure with an actionable message."""


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    observed: str
    expected: str
    required: bool = True


@dataclass(frozen=True)
class RustDeskRelease:
    tag: str
    asset: str
    url: str
    sha256: str


def fail(message: str) -> None:
    raise HarnessError(message)


def validate_host(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        fail("Host must not be empty.")
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        if not HOSTNAME_PATTERN.fullmatch(candidate):
            fail(f"Host is not a hostname or IP address: {value!r}")
    return candidate


def validate_port(value: int) -> int:
    if not 1 <= value <= 65535:
        fail(f"Port is outside the valid range: {value}")
    return value


def command_path(name: str) -> str | None:
    return shutil.which(name)


def completed(
    command: list[str], input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def run_remote(host: str, script: str) -> subprocess.CompletedProcess[str]:
    return completed(["ssh", *SSH_OPTIONS, host, "sh -s"], script)


def run_remote_tty(host: str, script: str) -> int:
    command = ["ssh", *SSH_OPTIONS, "-tt", host, f"sh -lc {shlex.quote(script)}"]
    return subprocess.run(command, check=False).returncode


def remote_status_script() -> str:
    return """set -u
field() { printf '%s\\t%s\\n' "$1" "$2"; }
field hostname "$(hostnamectl --static 2>/dev/null || hostname)"
field fedora "$(rpm -E %fedora 2>/dev/null || printf unknown)"
field architecture "$(uname -m)"
field default_target "$(systemctl get-default 2>/dev/null || printf unknown)"
if rpm -q --quiet rustdesk; then
  field rustdesk "$(rpm -q rustdesk)"
else
  field rustdesk absent
fi
for unit in sshd tailscaled docker netdata gdm gnome-remote-desktop; do
  field "unit.${unit}" "$(systemctl is-active "$unit" 2>/dev/null || printf unknown)"
done
if command -v ss >/dev/null 2>&1 && ss -lnt '( sport = :3389 )' | grep -q ':3389'; then
  field rdp_listener active
else
  field rdp_listener inactive
fi
graphical_sessions=0
for session in $(loginctl list-sessions --no-legend 2>/dev/null | awk '{ print $1 }'); do
  properties="$(loginctl show-session "$session" -p Class -p Type 2>/dev/null || true)"
  case "$properties" in
    *"Class=user"*)
      case "$properties" in
        *"Type=wayland"*) graphical_sessions=$((graphical_sessions + 1)) ;;
      esac
      ;;
  esac
done
field graphical_sessions "$graphical_sessions"
"""


def parse_status(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        key, separator, value = line.partition("\t")
        if separator:
            values[key] = value
    return values


def emit_checks(checks: list[Check], json_output: bool) -> int:
    if json_output:
        print(json.dumps([asdict(check) for check in checks], indent=2, sort_keys=True))
    else:
        for check in checks:
            state = "PASS" if check.passed else "WARN" if not check.required else "FAIL"
            print(f"[{state}] {check.name}: {check.observed} (expected {check.expected})")
    return 0 if all(check.passed or not check.required for check in checks) else 1


def doctor(args: argparse.Namespace) -> int:
    checks: list[Check] = []
    for name in ("ssh", "uv", "sdl-freerdp"):
        path = command_path(name)
        checks.append(Check(f"local {name}", path is not None, path or "missing", "installed"))
    brew = command_path("brew")
    checks.append(Check("local Homebrew", brew is not None, brew or "missing", "available for repair", False))

    remote = run_remote(args.host, remote_status_script())
    if remote.returncode != 0:
        detail = remote.stderr.strip() or remote.stdout.strip() or "no output"
        checks.append(Check("remote SSH", False, detail, "reachable through SSH configuration"))
        return emit_checks(checks, args.json)

    values = parse_status(remote.stdout)
    checks.extend(
        [
            Check("remote hostname", bool(values.get("hostname")), values.get("hostname", "missing"), "reported"),
            Check("remote Fedora", values.get("fedora") == "44", values.get("fedora", "missing"), "44"),
            Check("remote architecture", values.get("architecture") == "aarch64", values.get("architecture", "missing"), "aarch64"),
            Check("remote RDP listener", values.get("rdp_listener") == "active", values.get("rdp_listener", "missing"), "active"),
            Check("remote RustDesk", values.get("rustdesk") != "absent", values.get("rustdesk", "missing"), "installed after RustDesk test", False),
        ]
    )
    for unit in ("sshd", "tailscaled", "docker", "netdata", "gdm", "gnome-remote-desktop"):
        value = values.get(f"unit.{unit}", "missing")
        checks.append(Check(f"remote {unit}", value == "active", value, "active"))
    sessions = values.get("graphical_sessions", "0")
    checks.append(Check("remote graphical session", sessions.isdigit() and int(sessions) >= 1, sessions, "at least one remote session"))
    return emit_checks(checks, args.json)


def install_client(args: argparse.Namespace) -> int:
    client = command_path("sdl-freerdp")
    if client:
        print(f"FreeRDP is already available at {client}.")
        return 0
    brew = command_path("brew")
    if not brew:
        fail("Homebrew is unavailable. Install Homebrew, then rerun this command.")
    command = [brew, "install", "freerdp"]
    if args.dry_run:
        print("Would run:", shlex.join(command))
        return 0
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        return result.returncode
    if not command_path("sdl-freerdp"):
        fail("Homebrew finished, but sdl-freerdp is still unavailable. Check Homebrew output.")
    print("FreeRDP installation completed and sdl-freerdp is available.")
    return 0


def connect_rdp(args: argparse.Namespace) -> int:
    client = command_path("sdl-freerdp")
    if not client:
        fail("sdl-freerdp is unavailable. Run install-rdp-client first.")
    command = [
        client,
        f"/v:{args.rdp_host}:{args.port}",
        "/from-stdin",
        "+dynamic-resolution",
        "+clipboard",
        "/network:auto",
    ]
    if args.dry_run:
        print("Would run:", shlex.join(command))
        return 0
    return subprocess.run(command, check=False).returncode


def fetch_rustdesk_release() -> RustDeskRelease:
    request = urllib.request.Request(
        RUSTDESK_RELEASE_API,
        headers={"User-Agent": "betty-desktop-harness/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        fail(f"Could not read official RustDesk release metadata: {error}")
    assets = [
        asset for asset in payload.get("assets", [])
        if RUSTDESK_ASSET_PATTERN.fullmatch(asset.get("name", ""))
    ]
    if len(assets) != 1:
        fail(f"Expected one ARM64 Fedora RPM, found {len(assets)}.")
    asset = assets[0]
    digest_match = SHA256_PATTERN.fullmatch(asset.get("digest", ""))
    if not digest_match:
        fail("The official RustDesk asset did not provide a SHA-256 digest.")
    url = asset.get("browser_download_url", "")
    if not url.startswith("https://github.com/rustdesk/rustdesk/releases/download/"):
        fail("The RustDesk asset URL is not an official release download URL.")
    return RustDeskRelease(
        tag=str(payload.get("tag_name", "unknown")),
        asset=asset["name"],
        url=url,
        sha256=digest_match.group(1),
    )


def validate_asset(asset: str) -> str:
    if not RUSTDESK_ASSET_PATTERN.fullmatch(asset):
        fail("RustDesk asset name did not pass validation.")
    return asset


def rustdesk_stage_script(release: RustDeskRelease) -> str:
    asset = validate_asset(release.asset)
    return f"""set -eu
RUSTDESK_URL={shlex.quote(release.url)}
RUSTDESK_SHA256={shlex.quote(release.sha256)}
RUSTDESK_ASSET={shlex.quote(asset)}
stage_dir="$HOME/Downloads/betty-desktop-harness"
destination="$stage_dir/$RUSTDESK_ASSET"
partial="$destination.part.$$"
mkdir -p "$stage_dir"
trap 'rm -f "$partial"' EXIT
curl --fail --location --retry 3 --connect-timeout 15 --max-time 900 "$RUSTDESK_URL" --output "$partial"
printf '%s  %s\\n' "$RUSTDESK_SHA256" "$partial" | sha256sum --check --status -
mv "$partial" "$destination"
sha256sum "$destination"
"""


def rustdesk_stage(args: argparse.Namespace) -> int:
    release = fetch_rustdesk_release()
    print(f"Official RustDesk release: {release.tag}")
    print(f"ARM64 RPM: {release.asset}")
    print(f"Verified SHA-256: {release.sha256}")
    if args.dry_run:
        print("Would download and checksum-verify the RPM on Betty. No package would be installed.")
        return 0
    result = run_remote(args.host, rustdesk_stage_script(release))
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr.strip() or "RustDesk staging failed.", file=sys.stderr)
    return result.returncode


def remote_artifact_script(asset: str, command: str) -> str:
    asset = validate_asset(asset)
    return f"""set -eu
asset={shlex.quote(asset)}
artifact="$HOME/Downloads/betty-desktop-harness/$asset"
test -f "$artifact"
{command}
"""


def verify_artifact_command(sha256: str) -> str:
    return (
        f"printf '%s  %s\\n' {shlex.quote(sha256)} \"$artifact\" | "
        "sha256sum --check --status -\n"
        "rpm --checksig \"$artifact\""
    )


def rustdesk_preview(args: argparse.Namespace) -> int:
    release = fetch_rustdesk_release()
    verify = run_remote(
        args.host,
        remote_artifact_script(release.asset, verify_artifact_command(release.sha256)),
    )
    if verify.stdout:
        print(verify.stdout, end="")
    if verify.returncode != 0:
        print(verify.stderr.strip() or "Run rustdesk-stage first.", file=sys.stderr)
        return verify.returncode
    if args.dry_run:
        print("Would request an interactive remote sudo DNF preview.")
        return 0
    script = remote_artifact_script(
        release.asset,
        'exec sudo dnf --refresh --assumeno install "$artifact"',
    )
    return run_remote_tty(args.host, script)


def rustdesk_install(args: argparse.Namespace) -> int:
    if not args.apply:
        fail("Refusing package installation without --apply.")
    release = fetch_rustdesk_release()
    script = remote_artifact_script(
        release.asset,
        f'{verify_artifact_command(release.sha256)}\nsudo dnf install "$artifact" && rpm -q rustdesk',
    )
    return run_remote_tty(args.host, script)


def self_test(_: argparse.Namespace) -> int:
    assert validate_host("betty") == "betty"
    assert validate_host("100.119.71.22") == "100.119.71.22"
    try:
        validate_host("betty; rm -rf /")
    except HarnessError:
        pass
    else:
        fail("Host validation accepted shell syntax.")
    assert validate_port(3389) == 3389
    assert validate_asset("rustdesk-1.4.9-0.aarch64.rpm").endswith(".aarch64.rpm")
    print("Self-test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--host", default=DEFAULT_HOST, help="Betty SSH host. Defaults to BETTY_HOST or betty.")
    result.add_argument("--rdp-host", default=DEFAULT_RDP_HOST, help="Betty RDP host. Defaults to BETTY_RDP_HOST or BETTY_HOST.")
    result.add_argument("--port", default=DEFAULT_RDP_PORT, type=int, help="RDP port. Defaults to BETTY_RDP_PORT or 3389.")
    result.add_argument("--dry-run", action="store_true", help="Show a mutating action without running it.")
    result.add_argument("--json", action="store_true", help="Print doctor results as JSON.")
    actions = result.add_subparsers(dest="action", required=True)
    actions.add_parser("doctor", help="Check Mac and Betty prerequisites without changing state.")
    actions.add_parser("install-rdp-client", help="Install FreeRDP only when sdl-freerdp is missing.")
    actions.add_parser("connect-rdp", help="Open RDP without passing credentials on the command line.")
    actions.add_parser("rustdesk-stage", help="Download and verify the official RustDesk ARM64 RPM.")
    actions.add_parser("rustdesk-preview", help="Verify the RPM and preview its remote DNF transaction.")
    install = actions.add_parser("rustdesk-install", help="Install the staged RustDesk RPM.")
    install.add_argument("--apply", action="store_true", help="Confirm package installation.")
    actions.add_parser("self-test", help="Run deterministic input-guard checks.")
    return result


def main() -> int:
    args = build_parser().parse_args()
    args.host = validate_host(args.host)
    args.rdp_host = validate_host(args.rdp_host)
    args.port = validate_port(args.port)
    handlers = {
        "doctor": doctor,
        "install-rdp-client": install_client,
        "connect-rdp": connect_rdp,
        "rustdesk-stage": rustdesk_stage,
        "rustdesk-preview": rustdesk_preview,
        "rustdesk-install": rustdesk_install,
        "self-test": self_test,
    }
    return handlers[args.action](args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
