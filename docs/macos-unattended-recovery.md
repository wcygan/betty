# Betty unattended recovery: always available with power and internet

Decided 2026-10-30. This record owns Betty's power-loss recovery design and
supersedes the "keep FileVault on, automatic login off" guidance in the
[workstation plan](macos-agent-workstation.md) and option list in the
[headless recovery findings](macos-headless-recovery-findings-2026-10-29.md).
Status: settings applied; a restart test and a power-cut test passed
2026-10-30.

## Goal

As long as Betty has power and internet, it is reachable and working without
anyone touching it. After a power outage or crash it boots, logs in, rejoins
Tailscale, and starts the Rex server so the MacBook can reconnect to it.
Running sessions do not need to survive a restart; the services do.

## Decision

FileVault off, automatic login as the standard account `rat`, start up after
power failure, and Tailscale plus Rex as `rat`'s login items. The owner
explicitly accepted the security tradeoff below on 2026-10-30.

This is option 3 from the 2026-10-29 findings, with Rex in place of ChatGPT as
the service that must come back.

## Why not keep FileVault

With FileVault on, every restart stops at the disk-unlock screen until someone
enters a password. Nothing on the data volume runs before that, including
Tailscale, Rex and SSH as `rat`, and macOS disables automatic login.

macOS 26 can unlock FileVault over SSH at that pre-boot screen on Apple silicon
when Remote Login was already on. It still needs a person after every outage,
runs before Tailscale, and so works only from the LAN. Reports say wired
Ethernet worked first and Wi-Fi from 26.5. It fails the "no one touches it"
goal, so it is a fallback, not the design.

The open-source `tailscaled` LaunchDaemon only helps before GUI login; it cannot
unlock an encrypted disk, and Rex and agent credentials need a user session
anyway (see below).

## How others run always-on Mac minis

Homelab and Mac-hosting guides converge on the same three choices:

1. FileVault off, automatic login, "start up after power failure", apps as login
   items. The common answer for unattended recovery, and the one chosen here.
2. FileVault on, with a person unlocking after each outage, now possible over
   SSH on macOS 26. Hosting providers offer it but describe it as experimental.
3. A UPS to ride out short outages, used alongside either choice.

## Accepted tradeoff and mitigations

Apple silicon still encrypts the internal disk with a hardware key, so removing
the storage does not expose data. It no longer protects against someone who
takes the whole Mac: it boots and logs in as `rat`. Keychain items that
automatic login unlocks are reachable to anyone at the desktop.

Mitigations, in force or planned:

- `rat` remains a standard account. Administration needs `cygan`'s password,
  which stays outside Betty's agent session. No passwordless sudo.
- Credentials on `rat` stay scoped and revocable, as the
  [workstation plan](macos-agent-workstation.md) already requires; no personal
  vault or browser profile.
- Find My and Activation Lock on (to verify).
- Optional: lock the screen right after automatic login, so local access needs
  `rat`'s password while login items keep running. Not configured yet.

## Configuration

| Layer | Setting | Owner | Status 2026-10-30 |
| --- | --- | --- | --- |
| Power | `autorestart 1` (start up after power failure), `sleep 0` | `cygan` | Passed power-cut test 2026-10-30 |
| Disk | FileVault off | `cygan` | Verified over SSH (`fdesetup status`) |
| Login | Automatic login as `rat` | `cygan` | Passed restart test 2026-10-30 |
| Network | Wired Ethernet `en0` is the default route | — | Verified over SSH |
| Tailscale | Standalone `macsys` app, Open at Login for `rat` | `rat` | Passed restart test 2026-10-30 |
| Rex | Rex app at login for `rat`; its server joins the tailnet with built-in Tailscale as `betty-rex` | `rat` | Passed power-cut test 2026-10-30 |
| Rex config | `~/.config/rex` links to the dotfiles checkout | `rat` | Verified; dotfiles at `bc86408` |
| Agents | `claude`, `codex`, `pi` CLIs; `rex skill setup` and hooks | `rat` | Installed, signed in, and drove Rex panes 2026-10-30 ([checkpoint](macos-checkpoint-2026-10-30-rex.md)) |
| Backup power | UPS | owner | Optional; not present (`pmset -g ps` reports AC only) |

Rex's built-in Tailscale makes Rex its own tailnet device, independent of the
Tailscale app. Rex is reachable once the Rex app starts even if the app's VPN is
slow; SSH to Betty still depends on the Tailscale app. The Rex server admits
only the device owner by default, so do not pass
`--tailscale-allow-tailnet-members` or plain-HTTP `--allow-anonymous`.

Agent CLIs keep sign-in credentials in `rat`'s login Keychain, which automatic
login unlocks. A pre-login daemon could not use them; this is another reason
the design depends on a real `rat` session.

## Hardening review — 2026-10-30

Findings from read-only checks; none of these changes have been made yet.

| Issue | Finding | Proposed fix | Owner |
| --- | --- | --- | --- |
| Betty can reach the MacBook's Rex | The MacBook app serves its own Rex server over Tailscale (`foobar2-rex`). From a Betty pane, `rex -S https://foobar2-rex… whoami` returned `wcygan@github … from betty, acting as wcygan`: anything on Betty, including agents, can open a full shell on the vault-bearing MacBook. This breaks the boundary in the [workstation plan](macos-agent-workstation.md). | Turn off **Serve over Tailscale** in the MacBook app's Server settings; the phone then sees only Betty | owner |
| Screen never locks | `sysadminctl -screenLock` reports a 14,400 s delay and display sleep is off, so the auto-logged-in desktop stays open | Require the password immediately, then lock about a minute after login with a `rat` LaunchAgent (`pmset displaysleepnow`). Rex, SSH, Tailscale and agents keep running while locked; native Computer Use on a locked screen is intermittent | owner sets the password rule; agent adds the LaunchAgent |
| Tailscale keys expire | `betty` expires 2027-04-27 and `betty-rex` 2027-04-28; after that Betty drops off until someone signs in again | Disable key expiry for both devices in the Tailscale admin console, or set a calendar reminder | owner |
| Find My / Activation Lock | Not checked | Confirm on in `rat`'s or `cygan`'s Apple Account settings | owner |

## Recovery sequence

1. Power returns; firmware starts the Mac (`autorestart`).
2. macOS boots without a FileVault prompt and logs in `rat`.
3. Login items start Tailscale and Rex.
4. Rex's server rejoins the tailnet as `betty-rex` with its stored login.
5. The MacBook's Rex app reconnects; agents and terminals start fresh.

## Restart test — 2026-10-30 (passed)

The owner restarted Betty from its own desktop (a software restart, not a
power cut). Nobody touched Betty afterward. A MacBook watcher polled every
5 seconds over the LAN and Tailscale:

| Time after Betty dropped off | Stage |
| --- | --- |
| 0 s (14:36:36) | LAN SSH port stopped answering |
| 39 s | LAN SSH port answered |
| 40 s | SSH as `rat` over Tailscale worked; console user `rat`; Tailscale running |

Follow-up checks at 25 s of uptime: FileVault off, `who` showed only `rat` on
the console, and Tailscale reported Betty online. This proves automatic login
and Tailscale recovery. It does not exercise `autorestart` (power returning)
or Rex, which was not installed yet.

## Power-cut test — 2026-10-30 (passed)

The owner unplugged Betty and plugged it back in, then left it alone. The
MacBook watcher polled the LAN, SSH over Tailscale, and `rex -S betty ls`:

| Time after Betty dropped off | Stage |
| --- | --- |
| 0 s (15:29:28) | LAN SSH port stopped answering |
| 15 s | LAN SSH port answered |
| 26 s | SSH as `rat` over Tailscale; console user `rat`; Tailscale running; `betty-rex` answered `rex ls` |

Betty powered on without a button press, so `autorestart` works. Kernel boot
time was 15:29:28, the same second the watcher first saw it offline, so the
plug was out for only a few seconds rather than the suggested 30. `rat` cannot
read the logged shutdown cause, so the power loss itself rests on the owner's
report. The Rex server started at 20:29:43 UTC with both sessions restored:
layouts and labels came back, each pane with a fresh shell.

## Repeat test

Repeat after macOS, Rex, or Tailscale changes, or to measure a longer outage.

Run the same watcher from the MacBook, then cut power and leave Betty alone:

```sh
just recovery-watch --lan-host <Betty's wired LAN address>
```

It prints each stage's time after Betty drops off and exits 0 once SSH,
automatic login, Tailscale and the Rex server have all returned. Without
`--lan-host` it skips the boot-to-network stage. Use the wired (`en0`)
address: `betty.local` can resolve to the Wi-Fi interface instead.

Perform after Rex and the agent CLIs are installed. Do not touch Betty between
steps 1 and 3.

1. Disconnect Betty's power for at least 30 seconds, then reconnect it.
2. From the MacBook, time each stage separately: Tailscale ping and SSH as
   `rat`, `rex -S betty ls`, and a new Rex pane that runs a command.
3. Have each agent (Claude Code, Codex, Pi) open, read and close a pane on Betty.
4. Record which stages passed and how long each took. Claim only what was
   observed. Repeat once with a normal `sudo shutdown -r now` as `cygan`.

If a login item fails to recover in an observed test, consider a bounded
`rat` LaunchAgent for that one service, as the findings record suggested. Do
not add one before a failure is observed.

## Rollback

Turning FileVault back on (as `cygan`) restores disk-password protection and
disables automatic login; unattended recovery is lost again. The FileVault
recovery key stays in the owner's 1Password, never on Betty.

## Sources

- [Jeff Geerling: remote FileVault unlock in Tahoe](https://www.jeffgeerling.com/blog/2025/you-can-finally-manage-macs-filevault-remotely-tahoe/)
- [Apple: manage FileVault and SSH unlock](https://support.apple.com/guide/security/managing-filevault-sec8447f5049/web)
- [Greenmini: FileVault on hosted Mac servers](https://portal.greenmini.host/help/filevault-on-mac-servers-in-our-data-center)
- [vBoxx: FileVault on Mac servers](https://mac-hosting.vboxx.eu/help/filevault-on-mac-servers)
- [HomeTechOps: Mac mini auto power-on on Tahoe](https://hometechops.com/mac/mac-mini-auto-power-on-restart-tahoe)
- [Channels community: Mac mini recovery after power outage](https://community.getchannels.com/t/how-to-make-a-mac-mini-reboot-after-power-outage-and-have-channels-work-without-user-login/33528)
- [Tailscale macOS variants](https://tailscale.com/docs/concepts/macos-variants)
- [Rex remote access](https://www.superlogical.com/rex/docs/linux/remote-access)
