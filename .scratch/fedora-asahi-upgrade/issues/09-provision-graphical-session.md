# 09 — Provision and validate a Fedora Asahi graphical session

**What to build:** A usable Fedora Asahi desktop session on Betty without losing SSH-based recovery.

**Blocked by:** 08 — Choose the Fedora Asahi desktop transition.

**Status:** ready-for-agent

- [ ] Install the approved KDE or GNOME desktop components, or complete the approved desktop reinstall.
- [ ] Configure the selected display manager and graphical target.
- [ ] Provide a physical or virtual display suitable for remote access.
- [ ] Confirm the desktop session starts on the M2 Mac mini.
- [ ] Confirm SSH, Tailscale, Docker, and Netdata remain healthy.
- [ ] Record Wayland and Xorg session behavior for the selected remote-access design.

## Read-only preflight

```bash
ssh betty 'systemctl get-default; loginctl list-sessions || true'
ssh betty 'rpm -qa | grep -Ei "^(gnome|kde|plasma|xorg|gdm|sddm|mesa)" || true'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected evidence shows the approved package set, a reachable SSH path, and no service regression before the graphical target changes.

## Candidate package and display-manager commands

Run only the package commands selected in ticket 08. Use the package group name shown by `dnf group list --available`; do not guess a group.

```bash
sudo dnf group list --available | grep -Ei 'GNOME|KDE|Plasma'
sudo dnf install <approved-desktop-group> <approved-display-manager>
sudo systemctl enable <approved-display-manager>
sudo systemctl set-default graphical.target
sudo systemctl isolate graphical.target
```

Expected evidence is a display-manager session on the intended local or virtual display, while SSH remains usable from the Mac. If the graphical target fails, restore `multi-user.target` from the console:

```bash
sudo systemctl set-default multi-user.target
sudo systemctl isolate multi-user.target
```

## Session validation

```bash
ssh betty 'systemctl get-default; systemctl is-system-running; sudo systemctl --failed --no-legend'
ssh betty 'sudo systemctl is-active sshd tailscaled docker; curl -fsS http://127.0.0.1:19999/api/v1/info | head -c 200'
```

Record whether the session is Wayland or Xorg and whether a physical display, dummy display, or virtual display is present. This evidence gates ticket 10.

## Resources

- [Asahi Fedora documentation](https://asahilinux.org/fedora/)
- [Asahi FAQ: Wayland and Xorg](https://asahilinux.org/docs/project/faq/)
- [RustDesk Linux headless requirements](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/)
