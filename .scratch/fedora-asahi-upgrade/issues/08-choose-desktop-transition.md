# 08 — Choose the Fedora Asahi desktop transition

**What to build:** An approved desktop strategy with a rollback plan that preserves Betty’s headless recovery path.

**Blocked by:** 07 — Validate Fedora 44 and restore repository access.

**Status:** complete

- [x] Select a remote desktop design compatible with Fedora 44 and the no-monitor requirement.
- [x] Confirm the desktop choice supports the M2 Mac mini.
- [x] Document the impact on boot, display management, storage, services, and remote access.
- [x] Define rollback and SSH recovery criteria before changing the host.

## Initial graphical baseline

Before Step 9, Betty had no GNOME, KDE, Xorg, GDM, SDDM, or RustDesk packages.
It had Mesa driver libraries, but no desktop shell or display manager. Its
default target was `multi-user.target`.

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

## Decision baseline

At `2026-08-12T18:57:44Z`, Betty ran Fedora `44` on `aarch64` with
`multi-user.target`. SSH, Tailscale, and Docker were active. The installed
groups were `container-management` and `headless-management`. `gdm` and `sddm`
were not installed or enabled. The available root filesystem space was `291G`.
Both Immich mounts remained absent.

Fedora Asahi Remix supports M2 Mac minis. Its current documentation identifies
KDE Plasma as its flagship Wayland desktop, while Server remains the headless
variant. Fedora Asahi does not document conversion of an installed Server image
to a desktop variant.

OpenAI now documents its ChatGPT desktop app for Linux preview on Fedora `44`
and `aarch64`. The app includes Codex and uses XWayland by default in a Wayland
session. This supersedes the older research conclusion that no official Linux
desktop package exists.

## Transition research

See [`docs/research-asahi-desktop-transition.md`](../../docs/research-asahi-desktop-transition.md).
See [`docs/gnome-rustdesk-headless-transition.md`](../../docs/gnome-rustdesk-headless-transition.md)
for the proposed GNOME, GDM, Xorg, RustDesk, and ChatGPT design. The proposal
was approved on 2026-08-12 and later invalidated by the live test.
The earlier KDE inventory confirms that desktop groups add a full session, not
only graphics drivers. The selected proposal requires a new transaction preview
for the current GNOME group, GDM, Xorg, and the Xorg dummy driver. It will leave
the installed `fedora-asahi-remix-release-identity-server` package in place, so
it does not convert Betty into the separately installed Fedora Asahi GNOME
variant. Only a clean GNOME installation uses the documented Asahi desktop
deployment path.

## Approved decision and evidence

The user approved an in-place GNOME, GDM, Xorg, Xorg-dummy-driver, and
RustDesk-headless design on 2026-08-12. This remains an experimental Fedora
Server conversion, not an Asahi desktop-variant conversion.

The approved design was invalidated by the Step 9 live test. Fedora's official
Fedora 43 Wayland-only GNOME change removed the GNOME X11 session. It also says
that GDM itself requires Wayland. RustDesk documents that remote login-screen
access requires X11. Therefore, GNOME plus GDM cannot provide the documented
RustDesk X11 login path on Betty's Fedora 44 system. Do not mark a replacement
design as approved until it has an explicit remote login and virtual-display
strategy.

At `2026-08-12T22:31:41Z`, Betty reported Fedora `44`, ARM64, kernel
`7.1.6-400.asahi.fc44.aarch64+16k`, and `multi-user.target`. The root
filesystem had `291G` free. SSH, Tailscale, Docker, and Netdata were active.
No graphical packages or failed system units were reported. Both Immich mounts
were absent and the Immich Compose project had no running containers.

At `2026-08-12T22:31:41Z`, DNF identified the hidden `gnome-desktop` group.
Its mandatory packages include GDM, GNOME Shell, the GNOME session, Nautilus,
and the GNOME control center. `xorg-x11-server-Xorg` and
`xorg-x11-drv-dummy` are available for ARM64 Fedora 44.

The superseded design and its rollback procedure are in
[`docs/gnome-rustdesk-headless-transition.md`](../../docs/gnome-rustdesk-headless-transition.md).
The recovery path retains two SSH or Tailscale sessions. If a future graphical
boot fails, set `multi-user.target`, disable GDM, and reboot through SSH.

## Step 9 compatibility finding

At `2026-08-12T22:58:12Z`, the approved nonpersistent graphical-target test
started GDM and retained SSH, Tailscale, Docker, and Netdata. No failed units
were reported. `multi-user.target` remained the next-boot default.

Although `/etc/gdm/custom.conf` contains `WaylandEnable=false`, GDM started
`/usr/libexec/gdm-wayland-session gnome-session` and `/usr/bin/gnome-shell
--mode=gdm`. No Xorg process started. Fedora 44 supplies only
`/usr/share/wayland-sessions/gnome.desktop` for this GNOME installation.

This behavior is consistent with Fedora's official Wayland-only GNOME change.
The related RustDesk documentation is insufficient for Fedora 44 GNOME headless
login. The graphical target test must return to `multi-user.target` while the
replacement design is chosen.

## Replacement candidate: GNOME Remote Login over RDP

The installed `gnome-remote-desktop` package provides a supported no-monitor
candidate. GNOME documents Remote Login over RDP as a remote connection that
starts a headless greeter, then transfers the RDP connection into the user
session after login. This is the required remote-login behavior that RustDesk
cannot provide on Fedora 44 GNOME.

At `2026-08-12T23:03:48Z`, the temporary graphical target had stopped. Betty
was `running` in `multi-user.target`; GDM and the display manager were inactive;
and SSH, Tailscale, Docker, and Netdata remained active. No failed units or
graphical processes remained.

The replacement review found `/usr/bin/grdctl`, `gnome-remote-desktop.service`,
and the system remote-login configuration service. Both units were disabled. No
listener existed on port `3389`. The Tailscale interface is in the `trusted`
firewalld zone, while the physical interface is in the `FedoraServer` zone. The
replacement candidate must keep RDP accessible only over Tailscale and must not
open the physical network.

This design needs explicit approval before it sets RDP credentials, enables the
RDP backend or service, or changes firewall state. RustDesk may be tested later
inside the logged-in GNOME session, but it is not the remote-login dependency.

## Approved replacement: GNOME Remote Login over RDP

The user approved GNOME Remote Login RDP on 2026-08-12. It replaces the
incompatible RustDesk login-screen design.

GNOME Remote Login will provide the primary remote login and display path. It
uses GNOME Remote Desktop to create a headless GNOME login screen. It then
continues the RDP connection in the selected user's GNOME session.

Keep RDP available only through the Tailscale interface. Do not open TCP 3389
on the physical `end0` interface. Keep SSH and Tailscale active as the recovery
path. RustDesk is optional and can be evaluated only after the RDP session and
the ChatGPT desktop application work.

Before service enablement, restore the normal GDM configuration by removing the
obsolete `WaylandEnable=false` line. GNOME Remote Login requires native Wayland
support. This is a later, approval-gated root configuration change.

The next ticket must complete a root read-only RDP and firewalld preflight. It
must then set interactive RDP credentials, enable the system RDP backend, and
perform a nonpersistent graphical-target test from the Mac. Do not change the
next-boot default target until the remote RDP login and session handover pass.

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
