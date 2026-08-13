# 10 — Validate RustDesk and the ChatGPT desktop package

**What to build:** An official ChatGPT desktop application outcome on Betty,
with GNOME Remote Login RDP as the validated Mac remote-access path.

**Blocked by:** 09 — Provision and validate a Fedora Asahi graphical session.

**Status:** in-progress

- [x] Record why RustDesk is optional and not the remote-login dependency.
- [x] Validate Mac-to-Betty GNOME Remote Login RDP over Tailscale.
- [x] Test screen display, keyboard input, and clipboard transfer.
- [x] Record the Wayland, Xorg, virtual-display, and GDM result.
- [x] Verify the official ChatGPT Linux ARM64 package for Fedora 44.
- [ ] Download the official ARM64 RPM, verify its package signature, and preview its DNF transaction.
- [ ] Install and test the package only if its official support and graphical requirements are confirmed.
- [ ] Keep SSH as the recovery path if either graphical test fails.

## Step 9 replacement result

RustDesk is not required for Betty's remote access. Its documented X11 login
screen requirement is incompatible with Fedora 44's Wayland-only GNOME. Step 9
validated GNOME Remote Login RDP over Tailscale instead. The Mac FreeRDP client
connected, completed the RDP credential exchange, displayed the GNOME login
screen, and handed off to a remote Wayland GNOME session for `wcygan`.

The user confirmed working screen display, mouse input, keyboard input, and
clipboard transfer. Keep SSH as the recovery path. RustDesk is an optional
post-install experiment and is not an acceptance requirement for this ticket.

The user requested a RustDesk evaluation before the ChatGPT package work.
The reviewed outcome is documented in
[`docs/rustdesk-role-and-test-plan.md`](../../docs/rustdesk-role-and-test-plan.md).
RustDesk can be tested against the current logged-in Wayland session. It cannot
replace RDP for a fresh boot or GNOME login screen on Fedora 44. Do not disable
RDP or SSH during this evaluation.

## Cross-device desktop harness

The repository now provides `scripts/betty_desktop.py` and a `justfile`. The
portable `uv` script runs read-only Mac and Betty checks through `just doctor`.
It also provides separate commands to stage, verify, preview, and install the
official RustDesk ARM64 RPM. The install command requires a remote interactive
sudo prompt.

At `2026-08-12`, `just doctor` passed for SSH, FreeRDP, Fedora 44 ARM64, the
RDP listener, SSH, Tailscale, Docker, Netdata, GDM, GNOME Remote Desktop, and
one remote Wayland session. RustDesk remained absent. The harness dry-run
selected the official RustDesk `1.4.9` ARM64 RPM and its published SHA-256
digest. It did not download or install the package.

Read [`docs/betty-desktop-harness.md`](../../docs/betty-desktop-harness.md)
before any mutating harness command. Keep the new command surface under review
until a complete RustDesk connection and recovery test has passed.

## Current ChatGPT package preflight

At `2026-08-12T21:27:41-05:00`, Betty reported Fedora `44` on `aarch64` with
`290G` free on the root filesystem. The `chatgpt` package was not installed.
SSH, Tailscale, Docker, Netdata, GDM, and GNOME Remote Desktop were active.

OpenAI's current Linux desktop documentation lists Fedora 43 and 44 with ARM64
support. It provides an official Fedora ARM64 RPM and says the installed package
configures the signed OpenAI package repository for updates. The application
includes ChatGPT, projects, local files, and Codex.

At `2026-08-12T21:28:00-05:00`, the official ARM64 RPM URL returned HTTP 200,
the expected RPM media type, a `365320805` byte length, and a current ETag. The
next approval-gated action downloads this package to the user's Downloads
directory. It then checks its RPM signature and previews the DNF transaction.
Do not install the package during that preflight.

## Read-only package and session checks

```bash
ssh betty 'uname -m; rpm -q rustdesk || true; systemctl get-default'
ssh betty 'loginctl list-sessions; echo "DISPLAY=$DISPLAY WAYLAND_DISPLAY=$WAYLAND_DISPLAY XDG_SESSION_TYPE=$XDG_SESSION_TYPE"'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected architecture is `aarch64`. Before installation, RustDesk may be absent and the display variables may be empty in an SSH shell.

## RustDesk verification commands

Download the ARM64 Fedora RPM from the official RustDesk release page. Do not use an unverified mirror.

```bash
sha256sum ./rustdesk-*.rpm
rpm --checksig ./rustdesk-*.rpm
sudo dnf install ./rustdesk-*.rpm
rpm -q rustdesk
```

Expected evidence is a valid checksum or release signature and an installed ARM64 package. Test the Mac-to-Betty connection over the private network, then record screen capture, keyboard input, clipboard, reconnect, and unattended-access results.

RustDesk's documented Linux headless mode requires a desktop environment, Xorg, and GDM. A Wayland-only session or an SSH-only shell does not prove graphical RustDesk support.

## ChatGPT package verification commands

Check the official OpenAI download page at the time of the test. Do not install a package from a third-party repository.

```bash
curl -fsSL https://chatgpt.com/download/ | grep -iE 'linux|fedora|arm64' || true
```

As of the research date, the official page listed macOS and Windows desktop downloads, not a Fedora ARM64 Linux installer. Record the page result and keep ChatGPT on the Mac if no official package is published.

## Troubleshooting commands

```bash
ssh betty 'sudo journalctl -u rustdesk -b --no-pager || true'
ssh betty 'sudo systemctl status rustdesk --no-pager || true'
ssh betty 'sudo journalctl -b -p warning..alert --no-pager'
```

Preserve SSH as the recovery channel. Remove the package or revert the desktop change only through an approved rollback procedure if the graphical test harms the host.

## Resources

- [RustDesk Fedora and Linux installation](https://rustdesk.com/docs/en/client/linux/)
- [RustDesk advanced settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/)
- [RustDesk ARM64 releases](https://github.com/rustdesk/rustdesk/releases)
- [OpenAI ChatGPT download](https://chatgpt.com/download/)
