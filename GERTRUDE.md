# Gertrude

## Nix resource limits (2026-09-27)

Gertrude is a Raspberry Pi 3 Model B with 907 MiB of usable RAM and a 512 MiB
swap file. After it became unresponsive, the previous boot's logs showed
multiple Nix and npm processes, blocked Nix tasks, and out-of-memory events.
Memory pressure is a likely contributor, but the logs do not prove a single
root cause.

Gertrude uses Determinate Nix 3.12.0 (Nix 2.32.1). Its generated
`/etc/nix/nix.conf` must not be edited directly. The following overrides were
added to `/etc/nix/nix.custom.conf` on Gertrude:

```ini
# Keep local builds serial on this 1 GiB Raspberry Pi.
max-jobs = 1
cores = 1
```

Previously, `max-jobs` was `4` and `cores` was `0` (all four CPU cores).
`eval-cores` was already `1`. The original custom file is backed up on
Gertrude as `/etc/nix/nix.custom.conf.bak-20260927`.

`max-jobs = 1` permits one local Nix build at a time. `cores = 1` tells each
builder to use one core, but build scripts must honor that request. These
settings do not cap RAM or prevent separate Nix evaluations and npm processes
from running at the same time. A single large build can still exhaust memory.

### Verification

The custom file was changed while the socket-activated Nix daemon was stopped.
The daemon started six seconds later, so no reboot or further restart was
needed. `nix config show` reported both limits as `1`, and a three-derivation
smoke test completed. Its two independent builds ran one after the other.
There were no new out-of-memory kernel messages after the test; SSH, Tailscale,
and NetworkManager remained active.

Check the effective settings:

```sh
ssh gertrude 'nix config show | grep -E "^(max-jobs|cores|eval-cores) ="'
```

During the next normal Nix update, watch memory and swap in another session:

```sh
ssh gertrude 'vmstat 2'
```

Afterward, check for out-of-memory events in the current boot:

```sh
ssh gertrude 'journalctl -k -b --no-pager | grep -Ei "out of memory|oom-kill|killed process"'
```

The smoke test confirms that Nix builds with the limits and schedules local
builds serially. The next real update is the useful test of whether its memory
use stays within Gertrude's capacity.

References: [Determinate Nix configuration](https://docs.determinate.systems/determinate-nix/)
and [Nix cores and jobs](https://nix.dev/manual/nix/2.32/advanced-topics/cores-vs-jobs).
