# Fedora Asahi desktop transition research

**Research date:** 2026-08-12
**Scope:** Fedora Asahi Remix 44 and an existing Fedora Asahi Server system.

## Finding

Fedora Asahi documents KDE Plasma, GNOME, Server, and Minimal as distinct
installation choices. KDE is its flagship desktop. KDE and GNOME include
Wayland sessions from first boot. Server and Minimal are for headless or custom
systems. The reviewed Asahi documentation does not provide a Server-to-KDE or
Server-to-GNOME conversion procedure.

Fedora documents a separate, generic package path. A text-only Fedora system
can install the X Window System and GNOME or KDE with DNF. This path adds a
desktop to the current installation. It does not change the system into an
Asahi desktop image or recreate its first-boot configuration.

| Choice | Support statement | Risk and result |
| --- | --- | --- |
| Reinstall KDE or GNOME | Fedora Asahi supplies both desktop choices. KDE is the flagship desktop. | This is the documented Asahi desktop deployment. It replaces the current system. |
| Add desktop packages to Server | Fedora documents this for Fedora systems. | This is a custom package and boot-target change. Asahi does not document it as a variant conversion. |
| Keep Server | Fedora Asahi supplies Server for headless systems. | This preserves the current service and recovery model. |

## M2 Mac mini assessment

Fedora Asahi states support for all M1 and M2 Mac mini systems. Its M2 feature
matrix lists installer support for the 2023 M2 and M2 Pro Mac mini models. The
matrix lists HDMI, Wi-Fi, and Bluetooth as available in `linux-asahi` for both
models. Test the actual monitor, cable, and display manager before relying on a
graphical recovery path.

## Recommendation

Choose a clean Fedora Asahi KDE installation when Betty needs a durable local
desktop. KDE is the supported flagship desktop choice. Preserve a tested SSH
and Tailscale path before the reinstall.

Use a Fedora package conversion only when a reinstall is not acceptable. Label
it a custom Server change. Keep `multi-user.target` recovery instructions and
validate local display, graphical login, SSH, and services before acceptance.

## Primary sources

1. [Fedora Asahi Remix](https://asahilinux.org/fedora/): Fedora 44, desktop and Server choices, Wayland, and M2 Mac mini support.
2. [Asahi M2 feature support](https://asahilinux.org/docs/platform/feature-support/m2/): M2 and M2 Pro Mac mini installer and peripheral status.
3. [Fedora: After the Installation](https://docs.fedoraproject.org/cs/fedora/f30/install-guide/install/After_Installation/): generic Fedora desktop package path.
