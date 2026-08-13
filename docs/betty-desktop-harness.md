# Betty desktop harness

## Purpose

The harness reduces repeated Mac-to-Betty desktop checks. It uses one portable
Python script and a small `just` command surface.

## Selected loop

```text
Mac readiness -> Betty health -> RDP connection -> desktop evidence -> retry
```

The previous loop used separate local and remote terminals. It also required
manual checks for FreeRDP, SSH, RDP, GDM, and RustDesk state.

## Commands

| Command | Side effect | Success evidence |
| --- | --- | --- |
| `just doctor` | None | Reports Mac tools and Betty service state. |
| `just connect-rdp` | Opens a local window | Starts `sdl-freerdp` without credentials in shell history. |
| `just install-rdp-client` | Mac package install | Installs FreeRDP only when `sdl-freerdp` is absent. |
| `just rustdesk-stage` | Downloads one RPM on Betty | Checks the official GitHub SHA-256 digest. |
| `just rustdesk-preview` | Refreshes DNF metadata | Shows an interactive root DNF preview. |
| `just rustdesk-install` | Installs one Fedora RPM | Reports the installed `rustdesk` package. |

Set `BETTY_HOST`, `BETTY_RDP_HOST`, and `BETTY_RDP_PORT` to change targets.
The script validates these values. It rejects shell syntax and invalid ports.

## Approval and recovery

`doctor` is safe to repeat. The install, stage, preview, and connection commands
are separate actions. The harness never passes passwords as command arguments.

Keep SSH connected during RDP and RustDesk work. Do not disable GNOME Remote
Login RDP while testing RustDesk. RustDesk cannot provide Betty's Wayland GDM
login after reboot.

## Validation

Run `just check` to test the Python input guards and the justfile formatting.
Run `just doctor` to test the live Mac-to-Betty read-only path.

## Capability promotion

Do not add a new project skill yet. The command surface is new and its RustDesk
install and reconnect evidence is not yet proven. Revisit skill promotion after
the documented RustDesk test has passed.
