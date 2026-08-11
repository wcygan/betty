# 10 — Validate RustDesk and the ChatGPT desktop package

**What to build:** A decision-backed remote desktop and ChatGPT application outcome from the Mac to Betty.

**Blocked by:** 09 — Provision and validate a Fedora Asahi graphical session.

**Status:** ready-for-agent

- [ ] Install the official ARM64 RustDesk package only after verifying its source and signature.
- [ ] Validate a Mac-to-Betty RustDesk session over the private network.
- [ ] Test screen capture, keyboard input, clipboard, reconnect, and unattended access behavior.
- [ ] Record any Wayland, Xorg, virtual-display, or GDM limitations.
- [ ] Verify whether an official ChatGPT Linux ARM64 package is available for the supported Fedora release.
- [ ] Install and test the package only if its official support and graphical requirements are confirmed.
- [ ] Keep SSH as the recovery path if either graphical test fails.

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
