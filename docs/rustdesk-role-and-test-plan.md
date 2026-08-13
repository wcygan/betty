# RustDesk role and test plan for Betty

**Status:** Planned evaluation. RustDesk is not installed.

## Decision

Use GNOME Remote Login RDP as Betty's boot and login path. Test RustDesk only
as an optional tool for an active `wcygan` GNOME desktop.

Do not disable GNOME Remote Login RDP during the RustDesk evaluation. Keep SSH
as the host recovery path.

## Why RustDesk cannot replace RDP now

Betty runs Fedora 44 GNOME with Wayland. Fedora removed GNOME X11 sessions and
requires Wayland for GDM. RustDesk describes Wayland support as experimental.
RustDesk also says that remote access to a Wayland login screen is unsupported.

After a reboot, Betty has no `wcygan` desktop until a user signs in. RustDesk
cannot perform that sign-in. RDP can create the headless GNOME greeter and hand
the connection to the user desktop.

Automatic login could make RustDesk available after boot. It would leave
`wcygan` logged in without an interactive local login. This design weakens the
host security boundary. Do not use it for Betty.

## What the RustDesk test can prove

The test can prove that RustDesk can connect to the current logged-in GNOME
Wayland session. It can test screen display, mouse input, keyboard input,
clipboard transfer, reconnect behavior, and access controls.

It cannot prove unattended boot-to-desktop access. It cannot prove access to
the GNOME login screen. It cannot replace SSH recovery.

## Test sequence

1. Download the ARM64 Fedora RPM from the official RustDesk release.
2. Verify the release checksum and RPM signature.
3. Preview the DNF transaction before installation.
4. Install the RPM after a separate approval.
5. Start RustDesk inside the current GNOME desktop.
6. Configure a permanent password and restrictive incoming permissions.
7. Connect from the Mac over Tailscale or a verified direct private path.
8. Test screen display, input, clipboard, and reconnect behavior.
9. Disconnect RDP only while SSH remains connected.
10. Record whether the RustDesk session survives that disconnect.
11. Reboot only after a separate approval. Test the boot and login boundary.

## Acceptance rule

Call RustDesk an optional active-session tool only if all active-session tests
pass. Do not call it Betty's primary remote access path unless a reboot test
shows a secure, supported login path. Current vendor documentation does not
support that claim for Fedora 44 GNOME.

## References

- [RustDesk Linux](https://rustdesk.com/docs/en/client/linux/)
- [RustDesk advanced settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/)
- [Fedora Wayland-only GNOME](https://fedoraproject.org/wiki/Changes/WaylandOnlyGNOME)
- [GNOME Remote Login](https://teams.pages.gitlab.gnome.org/Websites/help.gnome.org/gnome-help/remote-login.html)
