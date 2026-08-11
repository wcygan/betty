# 02 — Quiesce Immich and detach data drives

**What to build:** A clean, verified stopped state that allows the data drives to be removed before the operating system upgrade.

**Blocked by:** 01 — Create and validate upgrade recovery backup.

**Status:** ready-for-agent

- [ ] Stop the Immich Compose project without deleting named volumes or bind-mounted data.
- [ ] Confirm no Immich process or diagnostic process uses either data drive.
- [ ] Flush pending filesystem writes.
- [ ] Unmount the Immich data drive successfully.
- [ ] Unmount the external backup drive successfully.
- [ ] Confirm both mounts are absent before physical removal.
- [ ] Record that the root, boot, and EFI filesystems remain on the internal NVMe device.

## Current Betty locations

- Compose project: `/home/wcygan/Development/immich-infra`.
- Immich data mount: `/mnt/immich`.
- External backup mount: `/mnt/externalhd`.
- Persistent mount declaration: `/etc/fstab` contains `LABEL=immich-primary /mnt/immich ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2`.

The external backup disk is manually mounted and is not listed in `/etc/fstab`. The last observed devices were `/dev/sdb2` (`immich-primary`) at `/mnt/immich` and `/dev/sda2` (`externalhdd`) at `/mnt/externalhd`.

## Read-only preflight

```bash
ssh betty 'cd /home/wcygan/Development/immich-infra && docker compose ps'
ssh betty 'findmnt /mnt/immich /mnt/externalhd; lsblk -o NAME,MODEL,SIZE,FSTYPE,LABEL,MOUNTPOINTS'
ssh betty 'sudo fuser -vm /mnt/immich /mnt/externalhd || true'
```

Expected evidence shows the Immich containers before shutdown, both mounts, and no unexpected users of either mount. Treat any `fuser` process as a blocker until its owner is known.

## Quiesce and detach commands

```bash
cd /home/wcygan/Development/immich-infra
docker compose down --remove-orphans
sync
sudo fuser -vm /mnt/immich /mnt/externalhd || true
sudo umount /mnt/immich
sudo umount /mnt/externalhd
findmnt /mnt/immich /mnt/externalhd || true
lsblk -o NAME,FSTYPE,LABEL,MOUNTPOINTS | grep -E 'immich-primary|externalhdd|nvme0n1' || true
```

Expected responses are no running Immich containers, successful `umount` commands, no output from `findmnt`, and the root, boot, and EFI mounts still on `nvme0n1`.

Never run `docker compose down -v`. Never unplug a disk while `findmnt` still shows its mount or `fuser` reports users.

## Resources

- [Docker Compose down reference](https://docs.docker.com/reference/cli/docker/compose/down/)
- [findmnt manual](https://man7.org/linux/man-pages/man8/findmnt.8.html)
- [umount manual](https://man7.org/linux/man-pages/man8/umount.8.html)
