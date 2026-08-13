# 09 — Provision and validate a Fedora Asahi graphical session

**What to build:** A usable Fedora Asahi desktop session on Betty without losing SSH-based recovery.

**Blocked by:** 08 — Choose the Fedora Asahi desktop transition.

**Status:** complete

- [x] Install the approved KDE or GNOME desktop components, or complete the approved desktop reinstall.
- [x] Configure GNOME Remote Login RDP and its system backend.
- [x] Provide a Tailscale-only virtual desktop and remote login path.
- [x] Confirm the desktop session starts on the M2 Mac mini.
- [x] Confirm SSH, Tailscale, Docker, and Netdata remain healthy.
- [x] Record Wayland and Xorg session behavior for the selected remote-access design.

## Read-only preflight

```bash
ssh betty 'systemctl get-default; loginctl list-sessions || true'
ssh betty 'rpm -qa | grep -Ei "^(gnome|kde|plasma|xorg|gdm|sddm|mesa)" || true'
ssh betty 'sudo systemctl is-active sshd tailscaled docker'
```

Expected evidence shows the approved package set, a reachable SSH path, and no service regression before the graphical target changes.

## Candidate package and display-manager commands

Ticket 08 selected the hidden `gnome-desktop` group with GDM, Xorg, and the
Xorg dummy driver. The group installs GDM as a mandatory package. Do not enable
another display manager.

Run the root simulation before the package installation. It must show no
signature errors, no removals, and the expected package count and size.

```bash
sudo dnf --refresh --assumeno --setopt=group_package_types=mandatory install @gnome-desktop xorg-x11-server-Xorg xorg-x11-drv-dummy
```

Run the package install, GDM enablement, target change, and target isolation
only after separate approval. Expected evidence is a display-manager session on
the intended virtual display, while SSH remains usable from the Mac. If the
graphical target fails, restore `multi-user.target` through SSH:

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

## DNF transaction preview evidence

The approved read-only previews ran at `2026-08-12T22:31:41Z` and
`2026-08-12T22:31:58Z`.

The full group preview proposed `578` package installs, a `414 MiB` download,
and `2 GiB` additional installed size. It proposed no removals.

The mandatory-only preview proposed `295` package installs, a `244 MiB`
download, and `1 GiB` additional installed size. It proposed no removals. This
is the selected installation scope.

Both previews used unprivileged DNF and displayed repository metadata signature
warnings for `1password` and `tailscale-stable`, despite loading the repository
metadata and solving the transaction. This does not prove the root DNF trust
path. The next root-only simulation must complete without these warnings before
the installation approval is requested.

The root simulation completed after the user ran it on 2026-08-12. It proposed
the mandatory-only GNOME transaction with `295` installs, a `244 MiB` download,
and `1 GiB` additional installed size. It proposed `0` removals and displayed
no repository signature error. `Operation aborted by the user.` was expected
because `--assumeno` prevents changes. The package-installation gate is now
ready for explicit approval.

## Package installation and configuration evidence

The user approved and completed the package installation on 2026-08-12. The
DNF transaction ended with `Complete!` after `297` installed items. Its output
included `gdm`, `gnome-shell`, `gnome-session`, `xorg-x11-server-Xorg`, and
`xorg-x11-drv-dummy`.

At `2026-08-12T22:42:58Z`, Betty confirmed the installed package versions:

```text
gdm-50.2-1.fc44.aarch64
gnome-shell-50.4-1.fc44.aarch64
gnome-session-50.1-1.fc44.aarch64
xorg-x11-server-Xorg-21.1.24-1.fc44.aarch64
xorg-x11-drv-dummy-0.4.1-8.fc44.aarch64
```

The host remained `running` with `290G` root free. SSH, Tailscale, Docker, and
Netdata remained active. No failed units were reported. The Immich mounts
remained absent and the Immich Compose project remained stopped.

At the time of this check, GDM was enabled by its package installation and
inactive because Betty used `multi-user.target`. `graphical.target` depends on
`gdm.service`. The only installed GNOME session descriptor was `gnome.desktop`.

## Graphical-target compatibility result

The user approved a nonpersistent graphical-target test on 2026-08-12.
`WaylandEnable=false` was added under `[daemon]` in `/etc/gdm/custom.conf`.
`systemctl isolate graphical.target` then returned successfully.

At `2026-08-12T22:58:12Z`, `graphical.target`, GDM, and the display manager
were active. The next-boot default remained `multi-user.target`. SSH,
Tailscale, Docker, and Netdata remained active. No failed units were reported.
GDM created a `gdm-greeter` session on `tty1`.

The test did not create an X11 GDM login screen. It started
`/usr/libexec/gdm-wayland-session gnome-session` and `/usr/bin/gnome-shell
--mode=gdm`. No Xorg process was present. Fedora 44 provides only the GNOME
Wayland session descriptor. Fedora's official Fedora 43 Wayland-only GNOME
change says that GNOME X11 packages are removed and GDM itself requires
Wayland. RustDesk documents that remote login-screen access requires X11.

Therefore, the selected GNOME, GDM, Xorg, and dummy-driver design cannot meet
the documented RustDesk X11 login requirement on Fedora 44. Do not set
`graphical.target` as the default. Restore the active target to
`multi-user.target`, then return to Step 8 for a replacement design.

The temporary target was restored successfully at `2026-08-12T23:03:48Z`.

## Approved GNOME Remote Login RDP path

Step 8 approved GNOME Remote Login RDP on 2026-08-12. It replaces the failed
RustDesk X11 login design. GNOME Remote Login provides the needed headless
greeter and user-session handover without an HDMI display.

First, run a root read-only preflight for the system RDP backend and both
firewalld zones. Confirm that no existing TCP 3389 rule permits the physical
network. Then use an interactive root terminal to set RDP credentials. Do not
place credentials in a command argument or shell history.

After a separate approval, remove `WaylandEnable=false` from the GDM
configuration. Enable GNOME Remote Login RDP. Test `graphical.target` without
changing the next-boot default. Connect from the Mac over Tailscale and confirm
the login screen, session handover, input, clipboard, and SSH recovery path.

Set `graphical.target` as the default only after the RDP session test passes.
Do not open RDP on `end0`. RustDesk remains optional and is no longer a
pre-login access dependency.

### RDP preflight evidence

At `2026-08-12T18:08:44-05:00`, Betty still used `multi-user.target`.
`/usr/bin/grdctl` was installed. Both `gnome-remote-desktop.service` and
`gnome-remote-desktop-configuration.service` were disabled and inactive. No
TCP 3389 listener existed.

Both system services use the GNOME Remote Desktop system daemon and are wanted
by `graphical.target`. This confirms the service path without enabling it.

The remaining preflight requires an interactive root terminal. It must confirm
the RDP backend state and the TCP 3389 policy in both firewalld zones. Record
only the yes-or-no results. Do not use `--show-credentials`.

The root preflight completed on 2026-08-12. `grdctl --system status` reported
an inactive unit, disabled RDP, port `3389`, credential authentication, and no
configured TLS certificate, TLS key, RDP user name, or RDP password. It printed
that TPM credentials are unavailable and that GKeyFile storage is used instead.
This is an expected fallback notice, not a failed preflight.

`firewall-cmd --query-port=3389/tcp` returned `no` for both `FedoraServer` and
`trusted`. Both GNOME Remote Desktop system units remained disabled and
inactive. No firewalld change is needed for a Tailscale-only initial test.

At `2026-08-12T18:11:00-05:00`, the service account home was
`/var/lib/gnome-remote-desktop`. `openssl` was available. `winpr-makecert` was
not installed. Generate the required self-signed TLS certificate with OpenSSL
as the service account during the next approval-gated configuration step.

### GNOME Remote Login configuration and live-test evidence

The user approved configuration and the nonpersistent live test on 2026-08-12.
The RDP credential prompt accepted a user name and password through standard
input. The credential values were not recorded. The expected TPM fallback used
GKeyFile storage.

At `2026-08-12T19:12:09-05:00`, GDM and the GNOME Remote Desktop system service
were both enabled and active. TCP `3389` listened on all local addresses. The
next-boot default remained `multi-user.target`. SSH, Tailscale, Docker, and
Netdata remained active. No failed system unit was reported.

At the same test stage, GDM created a Wayland headless greeter on `tty1` with
`gnome-shell --mode=gdm`. This is the expected GNOME Remote Login source
session. The next acceptance check is a Mac RDP connection through Tailscale.

The physical-network and Tailscale firewalld checks must be recorded after the
connection test. Do not set `graphical.target` as the default until the Mac RDP
login and user-session handover pass.

### Mac RDP login and session-handover evidence

The Mac FreeRDP client connected over Tailscale on 2026-08-12. Its received TLS
fingerprint matched the fingerprint reported by `grdctl --system status`. An
obsolete local FreeRDP certificate record caused an initial host-key warning.
It was removed only after the verified fingerprint matched.

At `2026-08-12T21:25:55-05:00`, Betty was `running` and retained
`multi-user.target` as the next-boot default. SSH, Tailscale, Docker, Netdata,
GDM, and GNOME Remote Desktop were active. TCP 3389 listened locally. No failed
system unit was reported.

At `2026-08-12T21:26:00-05:00`, `loginctl` showed a remote Wayland
`gdm-password` session for `wcygan`. The session ran
`gnome-session --session=gnome` and `gnome-shell --mode=user`. This confirms
that GNOME Remote Login handed the Mac RDP connection from the greeter to the
user desktop without an HDMI display.

The remaining Step 9 manual checks are mouse input, keyboard input, and
clipboard transfer in the Mac RDP window. After they pass, request a separate
approval before setting `graphical.target` as the next-boot default.

The user confirmed mouse input, keyboard input, and clipboard transfer on
2026-08-12. Step 9 is complete. `graphical.target` remains a later separate
approval because the current live-test boot default is still `multi-user.target`.

## Resources

- [Asahi Fedora documentation](https://asahilinux.org/fedora/)
- [Asahi FAQ: Wayland and Xorg](https://asahilinux.org/docs/project/faq/)
- [RustDesk Linux headless requirements](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/)
