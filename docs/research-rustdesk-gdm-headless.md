# RustDesk, GDM, and Linux headless access

**Research date:** 2026-08-12  
**Scope:** Official RustDesk, Fedora, and systemd documentation only.

**Compatibility update:** Fedora's official Fedora 43 Wayland-only GNOME change
removes the GNOME X11 session and states that GDM itself requires Wayland. The
RustDesk X11 GDM login recipe is therefore not compatible with Fedora 44 GNOME.
The RustDesk documentation did not state this Fedora 43+ limitation.

## Finding

RustDesk Linux headless access is not a graphical-stack-free service. RustDesk
documents its `allow-linux-headless` option for systems with no displays. The
option requires a desktop environment, an Xorg server, and GDM. It defaults to
disabled. [RustDesk advanced settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/#allow-linux-headless)

RustDesk's official project wiki gives Fedora headless prerequisites. It names
the GNOME desktop group and `xorg-x11-drv-dummy`. The wiki says that only GNOME
is supported and XFCE might work. It does not list KDE. Therefore, KDE is not
a documented supported Fedora headless session for RustDesk.
[RustDesk Headless Linux Support](https://github.com/rustdesk/rustdesk/wiki/Headless-Linux-Support)

RustDesk has experimental Wayland support. However, remote access to the
login screen requires X11. RustDesk says that Wayland GDM login screens are
not supported. It directs users to configure GDM with `WaylandEnable=false`
when they need access after reboot or logout. [RustDesk Linux guide](https://rustdesk.com/docs/en/client/linux/#login-screen)

`graphical.target` starts a graphical login path. It pulls in
`multi-user.target`. `multi-user.target` is the non-graphical multi-user
target. `default.target` normally links to one of these targets. A target
does not install a desktop environment, Xorg, GDM, or RustDesk.
[systemd.special(7)](https://www.freedesktop.org/software/systemd/man/latest/systemd.special.html)

Fedora Server documents desktop installation as separate work. It then tells
the administrator to set `graphical.target` as the default target. Fedora also
notes that some desktops need `gdm.service` enabled. This confirms that a
target change alone does not install a graphical stack.
[Fedora Server: Adding a graphical interface](https://docs.fedoraproject.org/en-US/fedora-server/usecase-gui-addon/)

## Consequences for a headless Fedora Server host

| Question | Evidence-based answer |
| --- | --- |
| Can RustDesk show a desktop on a host with no monitor? | Yes, only with headless mode and its documented desktop, Xorg, and GDM prerequisites. Fedora guidance names GNOME and the dummy Xorg driver. |
| Does `graphical.target` add these prerequisites? | No. It selects the graphical-login target. Package installation and display-manager setup remain separate work. |
| Can a Wayland GDM login screen be controlled after reboot? | No. RustDesk documents this as unsupported. Fedora 44 GNOME cannot provide the suggested X11 GDM replacement. |
| Does RustDesk replace SSH for host recovery? | No source makes this claim. RustDesk requires a graphical stack for headless graphical access. Keep SSH as the recovery path. |
| Can RustDesk provide terminal access? | RustDesk documents an incoming-connection terminal option and a terminal persistence option. This does not prove a GUI-free service mode. [Settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/#enable-terminal) |

## Limits and uncertainty

- These sources state product and system behavior. They do not prove that the
  exact Fedora Asahi release, GPU driver, or attached-display state will work.
- RustDesk names the required components, but it does not define a supported
  Fedora package set or a tested version matrix for this host.
- RustDesk documents GNOME for Fedora headless support. It does not document
  KDE as a supported Fedora headless session. Do not infer KDE support from
  its use as a normal Fedora desktop.
- Fedora 43+ removes the GNOME X11 session. Its GDM requirement for Wayland
  makes RustDesk's documented X11 login path unavailable on Fedora 44 GNOME.
- The RustDesk X11 statement applies to the GDM login screen. It does not
  require every logged-in desktop session to use X11.
- A pre-login RustDesk test must verify GDM starts, Xorg is selected for GDM,
  and an incoming connection shows the login screen after a reboot.

## Sources

All sources were accessed on 2026-08-12.

1. [RustDesk: Advanced settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/)
2. [RustDesk: Headless Linux Support](https://github.com/rustdesk/rustdesk/wiki/Headless-Linux-Support)
3. [RustDesk: Linux](https://rustdesk.com/docs/en/client/linux/)
4. [systemd: systemd.special(7)](https://www.freedesktop.org/software/systemd/man/latest/systemd.special.html)
5. [Fedora Server: Adding a graphical interface](https://docs.fedoraproject.org/en-US/fedora-server/usecase-gui-addon/)
6. [Fedora: Wayland-only GNOME](https://fedoraproject.org/wiki/Changes/WaylandOnlyGNOME)
