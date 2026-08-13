# Linux ChatGPT and RustDesk feasibility

**Host scope:** Fedora Asahi Remix 44 Server, ARM64 (AArch64), SSH-only, with no graphical desktop.

**Research date:** 2026-08-11

## Conclusion

- The official ChatGPT desktop app for Linux is now available in preview. Fedora 44 and ARM64 are supported. The app includes ChatGPT, Work, projects, local files, and Codex.
- The host still needs a graphical session. An SSH-only host cannot run the desktop app without a desktop environment and a display source.
- RustDesk has Fedora RPM guidance and AArch64 release artifacts. The package can be tested on this host.
- RustDesk graphical headless access is not a GUI-free SSH service. RustDesk documents `allow-linux-headless`, but this option requires a desktop environment, Xorg, and GDM. Those components are absent from the stated host profile.
- SSH remains the direct management path. RustDesk is useful only after adding and maintaining a graphical stack, or after a separate test confirms that its terminal feature meets the need.

## Evidence and implications

| Area | Official evidence | Implication for this host |
| --- | --- | --- |
| ChatGPT desktop | [OpenAI Linux desktop documentation](https://learn.chatgpt.com/docs/linux/linux-app) lists Fedora 43 and 44 plus ARM64 support. It provides an ARM64 Fedora RPM. | Betty can install the official preview after it has a graphical desktop session. |
| RustDesk package | [RustDesk Linux guide](https://rustdesk.com/docs/en/client/linux/) recommends `.rpm` for Fedora or CentOS and says to use the native package when possible. | Fedora packaging is the right first test path. The host architecture still needs package and runtime validation. |
| RustDesk ARM64 builds | [RustDesk releases](https://github.com/rustdesk/rustdesk/releases) include an AArch64 (ARM64) download row and links to Fedora downloads. | An ARM64 client artifact exists. This does not prove that a GUI-free Fedora Server deployment works. |
| RustDesk headless mode | [RustDesk advanced settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/) says `allow-linux-headless` permits incoming connections without displays, but requires a desktop environment, Xorg server, and GDM. The default is `N`. | The current no-GUI host does not meet the documented prerequisites. Installing those components would change the host profile. |
| RustDesk terminal options | The same advanced-settings reference documents `enable-terminal` and `terminal-persistent=Y`. | Terminal access may be testable, but the documentation does not define a GUI-free RustDesk daemon mode. SSH is already available and has fewer moving parts. |
| Fedora Asahi platform | [Fedora Asahi Remix 44 announcement](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/) says the release brings Fedora Linux 44 to Apple Silicon, provides a Fedora Server variant for server and headless deployments, and allows existing Remix 42 or 43 systems to upgrade with the usual Fedora process. | The operating-system family supports this server profile. An upgrade may improve support, but it does not add a Linux ChatGPT desktop app or remove RustDesk's Xorg/GDM requirement. |

## Recommended decision

Use KDE Plasma for a graphical Betty deployment. The official ChatGPT Linux
preview supports Fedora 44 ARM64 and uses XWayland by default in a Wayland
session. Keep SSH as the recovery path. Install RustDesk only after the desktop
session works; its documented headless graphical mode still requires a desktop
environment, Xorg, and GDM.

## Sources

All sources were accessed on 2026-08-11.

1. [OpenAI — ChatGPT desktop app for Linux](https://learn.chatgpt.com/docs/linux/linux-app)
2. [RustDesk — Linux](https://rustdesk.com/docs/en/client/linux/)
3. [RustDesk — Advanced Settings](https://rustdesk.com/docs/en/self-host/client-configuration/advanced-settings/)
4. [RustDesk — GitHub Releases](https://github.com/rustdesk/rustdesk/releases)
5. [Fedora Magazine — Fedora Asahi Remix 44 is now available](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/)

## Fedora Asahi Remix support refresh (2026-08-11)

### Mac mini support

- The current Asahi page is based on Fedora Linux 44 and names M1 and M2 Mac mini models as supported.
- The page does not claim support for an M3 or M4 Mac mini. Treat those models as unverified until the project lists them.

Source: [Asahi Linux — Fedora Asahi Remix](https://asahilinux.org/fedora/).

### Fedora 42 to Fedora 44 in-place upgrade

- The Fedora Asahi Remix 44 release note says existing Remix 42 and 43 systems can use the usual Fedora upgrade process.
- The release note says GNOME Software cannot perform this upgrade. Use KDE Plasma Discover or DNF `system-upgrade`.
- Fedora's upgrade guide describes `dnf system-upgrade` as the command-line method and limits supported cross-release testing to one release, or two releases during the short grace period after a new release.
- Fedora's current release list names 43 and 44 as supported releases. Fedora 42 is therefore outside current Fedora support on this research date. A direct 42 to 44 upgrade is historical release-note guidance, not a current supported path. Move through a supported release or perform a clean install after taking a backup.

Sources: [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/), [Fedora DNF system upgrade guide](https://fedoraproject.org/wiki/DNF_system_upgrade), and [Fedora current releases](https://fedoraproject.org/wiki/Releases).

### Server, KDE, and GNOME variants

- Fedora Asahi Remix 44 provides KDE Plasma as the flagship desktop image, a GNOME image, a Fedora Server image for server and headless deployments, and a Minimal image.
- The Asahi page describes the desktop images as Wayland-first and the Server and Minimal images as the choices for headless or custom setups.
- These are separate install choices. The release note does not describe a variant switch during an in-place version upgrade.

Source: [Fedora Asahi Remix 44 release note](https://fedoramagazine.org/fedora-asahi-remix-44-is-now-available/).

### Switching an installed Server system to a desktop

- Fedora's general installation documentation says a text-only installation can gain a graphical desktop by installing the X Window System and GNOME or KDE with DNF, then enabling graphical login.
- This is a Fedora package-management path. The Asahi release note and Asahi Fedora page do not document or promise a Server-to-KDE/GNOME conversion procedure.
- Therefore, adding a desktop to an installed Asahi Server system is technically possible as a custom Fedora package change, but it is not an Asahi-documented variant conversion. Use a supported KDE or GNOME image for a clean desktop deployment; treat a Server conversion as an experimental change and keep an SSH recovery path.

Source: [Fedora Docs — After the Installation](https://docs.fedoraproject.org/cs/fedora/f30/install-guide/install/After_Installation/).

### Betty live verification (2026-08-11)

- Betty reports Fedora Asahi Remix 42 Server on AArch64. The installed release packages are `fedora-asahi-remix-release-common`, `fedora-asahi-remix-release-identity-server`, and `fedora-asahi-remix-release-server`.
- Betty has DNF5 `system-upgrade` support. The command exposes `download` and `reboot` actions.
- Release 44 repository metadata exposes `fedora-asahi-remix-release-server`, the matching server identity package, `asahi-platform-metapackage-desktop`, `asahi-platform-metapackage-plasma`, and ARM64 `kernel-16k` packages.
- The release 44 query loaded successfully after disabling the 1Password and Tailscale repositories. With those repositories enabled, DNF reported repository metadata signature errors and requested key imports.
- No GNOME, KDE, Xorg, GDM, SDDM, Mesa desktop, or RustDesk packages are installed. The default target is `multi-user.target`.

These checks show a plausible package-level path to Fedora 44 and a custom desktop addition. They do not prove that the full upgrade transaction will succeed. A privileged DNF preflight must review third-party repository keys, package removals, and the reboot path before execution.
