---
name: betty-desktop-upgrades
description: Use when planning or executing a Betty Fedora Asahi upgrade, Immich backup or drive detach, desktop transition, RustDesk test, or ChatGPT desktop evaluation.
---

# Betty Desktop Upgrades

Use this skill for operating-system upgrades and desktop changes on Betty. Preserve the SSH recovery path at every stage.

## Source of truth

Read the relevant ticket before action:

`.scratch/fedora-asahi-upgrade/issues/01-recovery-backup.md` through `10-validate-rustdesk-and-chatgpt.md`.

Read `docs/research-linux-chatgpt-rustdesk.md` for current support findings and official references.

Tickets are the execution plan. Live Betty state is authoritative over cached notes. Re-run read-only checks before any change.

## Dependency chain

Complete the tickets in this order:

`01 backup → 02 quiesce and detach → 03 repository preflight → 04 Fedora 43 → 05 validate → 06 Fedora 44 → 07 validate → 08 desktop decision → 09 graphical session → 10 RustDesk and ChatGPT`.

Do not start a ticket while its blocker is incomplete.

## Betty baseline

These values are starting assumptions. Verify them before use:

- Fedora Asahi Remix Server 42.
- ARM64 (`aarch64`) on an M2 Mac mini.
- Default target: `multi-user.target`.
- Immich deployment: `/home/wcygan/Development/immich-infra`.
- Immich data disk: `/mnt/immich`.
- External backup disk: `/mnt/externalhd`.
- Immich mount label: `immich-primary`.
- Third-party repository IDs: `1password` and `tailscale-stable`.

The external backup disk is exFAT. Unix ownership and mode bits are not reliable on that disk.

## Read-only first

Run these checks before a ticket action:

```bash
ssh betty 'hostnamectl --static; rpm -E %fedora; uname -r; uname -m; systemctl get-default'
ssh betty 'findmnt /mnt/immich /mnt/externalhd; df -h /mnt/immich /mnt/externalhd'
ssh betty 'cd /home/wcygan/Development/immich-infra && docker compose ps'
ssh betty 'sudo systemctl --failed --no-legend; sudo systemctl is-active sshd tailscaled docker'
```

Record the request, response, timestamp, and conclusion in the ticket evidence.

## Safety gates

- Keep a second SSH or Tailscale session open before a reboot.
- Create and validate a current database dump and asset backup before an operating-system change.
- Stop Immich with `docker compose down --remove-orphans`.
- Keep named Docker volumes by never adding `--volumes` or `-v` to `docker compose down`.
- Run `sync`, check `fuser`, and unmount both disks before physical removal.
- Keep root, boot, and EFI filesystems on the internal NVMe device.
- Review DNF removals, repository signatures, and target release before rebooting.
- Pause for user approval before backup writes, service shutdown, unmount, package changes, or reboot.
- Treat physical disk removal, desktop selection, local display checks, and Mac-to-Betty GUI tests as manual steps.

## Automation boundary

Safe automation includes read-only inspection, backup manifests, checksum checks, DNF transaction staging, health checks, and diagnostic collection.

Approval-gated automation includes database dumps, asset copies, service shutdown, unmounting, repository changes, package installation, display-manager changes, and reboot.

Manual work includes physically unplugging drives, choosing the desktop variant, confirming local graphical login, and testing RustDesk input and clipboard from the Mac.

## Desktop and remote-access rules

The supported Asahi variants are separate Server, KDE, and GNOME images. A Server-to-desktop conversion is an experimental Fedora package change, not an Asahi-documented variant switch.

Prefer Wayland on Asahi. RustDesk Linux headless mode documents a desktop environment, Xorg, and GDM requirement. An SSH shell alone does not prove graphical RustDesk support.

Keep ChatGPT on the Mac unless an official Fedora ARM64 Linux package is available from OpenAI at test time.

## Troubleshooting

Capture these outputs when a step fails:

```bash
sudo journalctl -b -p warning..alert --no-pager
sudo systemctl --failed --no-legend
sudo dnf history info last
sudo systemctl status sshd tailscaled docker --no-pager
```

Use the official references in the tickets for Fedora offline upgrades, Asahi support, Immich backup and restore, Docker Compose, RustDesk, and OpenAI downloads.

## Completion

A ticket is complete only when every acceptance checkbox has evidence and the next ticket's blocker is explicitly satisfied. Keep the host headless and recoverable until the desktop validation ticket passes.
