# GNOME Remote Login RDP design for Betty

**Status:** Approved design. Host configuration has not started.

## Purpose

Provide a no-monitor GNOME login and desktop session on Betty. Keep SSH and
Tailscale as the recovery path.

## Selected design

Use GNOME Remote Login through the GNOME Remote Desktop system RDP backend.
Connect from the Mac through Tailscale. Do not expose RDP on Betty's physical
network interface.

GNOME Remote Login creates a headless GNOME login screen. After sign-in, it
continues the same RDP connection in the selected user session. This makes an
HDMI display unnecessary for the first desktop session.

```text
Mac RDP client -> Tailscale -> GNOME Remote Desktop RDP
                                  -> headless GDM greeter
                                  -> GNOME user session
                                  -> ChatGPT desktop application
```

## Why this design

Fedora 44 GNOME is Wayland-only. The GDM test on Betty confirmed that
`WaylandEnable=false` did not select Xorg. RustDesk documents that its remote
login screen needs X11. Therefore, RustDesk cannot provide Betty's pre-login
remote path.

GNOME documents Remote Login as an RDP service for remote sign-in. It supports
the required headless login and session handover. It is the selected primary
remote access path. RustDesk can be tested later inside an active GNOME session.

## Security boundary

Keep TCP 3389 reachable only through `tailscale0`. Do not add a `FedoraServer`
zone rule for TCP 3389. The physical interface is `end0`.

Set RDP credentials only from an interactive root terminal. Do not put a user
name or password in shell history, ticket evidence, or chat output. Keep a
second SSH or Tailscale session connected during service and target tests.

## Rollout sequence

1. Inspect the system RDP backend and firewalld zones without changing state.
2. Generate a self-signed TLS key and certificate as `gnome-remote-desktop`.
3. Remove the obsolete GDM Xorg override.
4. Set RDP credentials through standard input as root.
5. Enable the GNOME system RDP backend and GDM.
6. Connect from the Mac through Tailscale.
7. Confirm the login screen, session handover, input, clipboard, and SSH.
8. Set the graphical target as the default only after the test passes.

The RDP backend requires a TLS key and certificate. Fedora's installed
`gnome-remote-desktop` documentation specifies this setup. Betty has OpenSSL,
so the configuration generates a self-signed certificate under the service
account. Verify the displayed fingerprint from the client during the test.

## Current test state

At `2026-08-12T19:12:09-05:00`, the system RDP backend and GDM were enabled
and active. TCP 3389 listened locally. The next-boot target remained
`multi-user.target`. A Wayland GDM greeter was active on `tty1`.

The next action is a Mac RDP connection through Tailscale. The RDP client must
support RDP Server Redirection because GNOME transfers the connection from the
remote login service to the greeter, then to the user session. GNOME lists
Thincast as a known working macOS client.

If the RDP test fails, isolate `multi-user.target` through SSH. Leave the
next-boot default at `multi-user.target` until a successful test permits it.

## References

- [GNOME Remote Login](https://teams.pages.gitlab.gnome.org/Websites/help.gnome.org/gnome-help/remote-login.html)
- [GNOME Remote Desktop](https://gitlab.gnome.org/GNOME/gnome-remote-desktop)
- [Fedora Wayland-only GNOME](https://fedoraproject.org/wiki/Changes/WaylandOnlyGNOME)
- [RustDesk Linux login screen](https://rustdesk.com/docs/en/client/linux/#login-screen)
