# 08 — Choose the Fedora Asahi desktop transition

**What to build:** An approved desktop strategy with a rollback plan that preserves Betty’s headless recovery path.

**Blocked by:** 07 — Validate Fedora 44 and restore repository access.

**Status:** ready-for-agent

- [ ] Decide between remaining Server, adding desktop packages, or reinstalling a supported KDE or GNOME image.
- [ ] Confirm the desktop choice supports the M2 Mac mini.
- [ ] Document the impact on boot, display management, storage, services, and remote access.
- [ ] Define rollback and SSH recovery criteria before changing the host.

## Current graphical baseline

Betty currently has no GNOME, KDE, Xorg, GDM, SDDM, Mesa desktop, or RustDesk packages. Its default target is `multi-user.target`.

```bash
ssh betty 'systemctl get-default; rpm -qa | grep -Ei "^(gnome|kde|plasma|xorg|gdm|sddm|rustdesk|mesa)" || true'
ssh betty 'sudo dnf group list --installed; sudo dnf group list --available | grep -Ei "GNOME|KDE|Plasma" || true'
```

Expected output confirms the current headless state and identifies the package groups available for an experimental conversion.

## Decision options

1. Keep the Server image and use SSH plus ChatGPT on a separate Mac.
2. Add a Fedora desktop package set and display manager. Treat this as an experimental Server conversion.
3. Reinstall a supported Fedora Asahi KDE or GNOME image after verifying the backup and recovery path.

The Asahi documentation describes Server, KDE, and GNOME as separate variants. It does not document a Server-to-desktop conversion. Select an option before running package or boot-target changes.

## Decision record commands

```bash
ssh betty 'rpm -E %fedora; uname -m; systemctl get-default'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Record the selected option, its display manager, its Wayland or Xorg requirement, its physical or virtual display source, and the SSH rollback test.

## Resources

- [Fedora Asahi Remix](https://asahilinux.org/fedora/)
- [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)
- [Fedora desktop after installation](https://docs.fedoraproject.org/en-US/fedora/latest/getting-started/)
