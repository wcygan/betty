# Checkpoint 2026-10-30: Betty is the always-on Rex host

Betty now hosts the Rex server that the MacBook and phone connect to, and it
recovers from a restart without anyone touching it. Agents run on Betty inside
Rex panes and can drive Rex themselves. Recovery design and its open tests live
in [unattended recovery](macos-unattended-recovery.md); this note records what
was set up and verified at this checkpoint.

## What works

| Area | State | Evidence |
| --- | --- | --- |
| Recovery | FileVault off, automatic login as `rat`, start after power failure | Restart test: back on Tailscale with `rat` logged in after ~40 s, no input |
| Rex server | Superlogical Rex Beta 0.1.0 (server `0.0.1793377904-ge6592f`) runs as `rat`; built-in Tailscale serves `betty-rex`; access limited to `wcygan@github` | `rex -S betty whoami` from the MacBook: `wcygan@github over tailscale … acting as rat` |
| Rex config | `~/.config/rex` links to the dotfiles checkout; five Ghostty-equivalent shortcuts | `rex -S betty -C betty keymap` lists them from `init.lua` |
| Shell | New Rex panes run Fish with Rex's own `rex` first on `PATH` | Checked in a fresh pane opened from the MacBook |
| MacBook | Connected client; Betty is its Rex home (`rex home set`) and a saved host; Switch Host works in the app | `rex -S betty client ls` |
| Phone | User reported it connects | Not connected when checked; not independently verified |
| Claude Code 2.1.314 | Signed in with the claude.ai account; Rex skill and session-start hook | Started in a Betty pane: saw the Rex hook, opened, read and closed a pane |
| Codex 0.165.0 | Signed in with ChatGPT; Rex skill; hook approved | Same test passed after the sandbox change below |
| Pi 1.4.0 | Signed in to OpenRouter and OpenAI; Rex skill (Pi has no hooks) | Same pane test passed |

## How it was installed

All as `rat`, without administrator rights:

- Rex Beta: copied from the MacBook to `~/Applications/Rex Beta.app`. It is
  notarized (Developer ID Superlogical, Inc., `AG92C3PT77`) and Gatekeeper
  accepts it. A user folder lets Rex update without an admin password. The owner
  enabled Rex's Tailscale and Remote Control and added Rex to Open at Login.
- Claude Code: Anthropic's native installer, into `~/.local/bin`.
- Pi: pi.dev's managed installer, into `~/.pi/agent`, linked from `~/.local/bin`.
- Codex: `npm install -g @openai/codex` into `~/.local`, the dotfiles npm
  prefix. Its one-day release-age rule can lag the MacBook's Homebrew copy.
- `rex skill setup`: Rex skill for all three agents, session-start hooks for
  Claude Code and Codex.
- Sign-in: done from the MacBook in a Betty Rex session. Codex was already
  signed in from earlier setup.

## Configuration changed on Betty

- `~/.codex/config.toml` gained `[sandbox_workspace_write] network_access = true`.
  Codex's default sandbox blocked the Rex server socket, so Codex could not
  drive Rex. The sandbox stays on; Betty still does not use the MacBook's
  `danger-full-access` template. Backup:
  `~/.local/state/betty-setup/codex-config.before-network-2026-10-30.toml`.
- Claude Code and Codex settings files were backed up to
  `~/.local/state/betty-setup/` before `rex skill setup` added its hooks.
- Superseded untracked drafts of two docs were moved from the Betty checkout to
  `~/.local/state/betty-setup/betty-docs-drafts-2026-10-30/` so it could update.

## Things to know

- Plain SSH sessions cannot read `rat`'s login Keychain. Over SSH,
  `claude auth status` reports "not logged in" and `gh` falls back to
  anonymous access (60 requests/hour, no GraphQL), which makes
  `./bootstrap.sh agent-skills` fail. Run credentialed work in a Rex pane,
  which runs in `rat`'s desktop session. On 2026-10-30 an SSH attempt left a
  recovery marker that `./bootstrap.sh recover --apply --yes` cleared after
  `--check` showed no partial install; the catalog then updated to
  `359fa13` (72 skills) from a Rex pane.
- Rex's agent skill tells agents to name their Rex session. Expect session
  labels to change when agents start tasks.
- Rex sessions do not survive a restart; the server and logins do.

## Still open

- Power-cut acceptance test with Rex and the agents installed (see
  [unattended recovery](macos-unattended-recovery.md)). It is the only test of
  `autorestart` and of Rex returning as a login item.
- Optional screen lock after automatic login, and Find My/Activation Lock check.
- Phone connection to be verified by the owner.
