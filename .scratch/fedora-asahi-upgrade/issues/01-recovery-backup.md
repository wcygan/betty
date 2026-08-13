# 01 — Create and validate upgrade recovery backup

**What to build:** A current, restorable recovery set for Betty before any operating system change.

**Blocked by:** None — can start immediately.

**Status:** complete

- [x] Create a current Immich PostgreSQL dump while the database is available.
- [x] Back up the Immich asset folders and the deployment configuration.
- [x] Back up Betty configuration and service definitions needed to restore SSH, Tailscale, Docker, and Netdata.
- [x] Store the recovery set on the external backup drive.
- [x] Verify archive integrity and record backup timestamps and sizes.
- [x] Confirm the backup includes both Immich metadata and asset files, not image files alone.

## Current Betty locations

- Immich deployment: `/home/wcygan/Development/immich-infra`.
- Immich source data: `/mnt/immich` on the `immich-primary` ext4 disk.
- Existing backup disk: `/mnt/externalhd` on the `externalhdd` exFAT disk.
- Existing backup roots: `/mnt/externalhd/immich-backup` and `/mnt/externalhd/immich-backups`.

The active Immich asset bind mount is `/mnt/immich/library` to `/data` in
`immich_server`. The `upload` and `profile` paths are absent on the live host.
Back up `library` and the logical PostgreSQL dump. Do not copy the raw PostgreSQL
data directory.

The live host has no `/etc/tailscale` or `/etc/docker` directory. Tailscale state
is in `/var/lib/tailscale`. Docker uses its packaged unit files and has no local
`/etc/docker` configuration. Netdata configuration is in the
`betty_netdataconfig` Docker volume.

Existing backup files are useful reference points. They do not prove that the current Immich database and assets are restorable.

Observed on 2026-08-11: `/mnt/immich` has about 3.1 TB free and `/mnt/externalhd` has about 1.2 TB free. The source disk reports about 391 GB used. Confirm these values again before copying because usage changes.

Known existing artifacts include:

- `/mnt/externalhd/immich-backup/database/immich-db-upgrade-pre-v3-20260702T104434-0500-v2.7.5.sql.gz` (about 180 MB).
- `/mnt/externalhd/immich-backups/2025-11-01_17-13-19/database.sql` (about 353 MB).
- `/mnt/externalhd/immich-backups/2025-11-01_17-13-19/library.tar.gz` (about 183 GB).

## Read-only reconnaissance

```bash
ssh betty 'findmnt /mnt/immich /mnt/externalhd; df -h /mnt/immich /mnt/externalhd'
ssh betty 'cd /home/wcygan/Development/immich-infra && docker compose ps'
ssh betty 'du -sh /mnt/immich/library'
ssh betty 'find /mnt/externalhd/immich-backup /mnt/externalhd/immich-backups -maxdepth 2 -type f -printf "%TY-%Tm-%Td %TH:%TM %s %p\\n" | sort'
```

Expected evidence includes both mounts, enough free space for the measured source data,
four running Immich containers, the active library size, and dated backup files.

The last observation had this shape; do not treat it as a current measurement:

```text
/dev/sdb2  3.6T  391G  3.1T  12%  /mnt/immich
/dev/sda2  1.9T  718G  1.2T  38%  /mnt/externalhd
```

## Live reconnaissance evidence

The checks below ran at `2026-08-11T23:24:10Z`.

```text
Host: betty
Fedora: 42
Kernel: 6.14.2-401.asahi.fc42.aarch64+16k
Architecture: aarch64
Default target: multi-user.target

/mnt/immich: /dev/sdb2, ext4, mounted read-write
/mnt/externalhd: /dev/sda2, exfat, mounted read-write
/mnt/immich: 3.6T total, 391G used, 3.1T free
/mnt/externalhd: 1.9T total, 718G used, 1.2T free

Immich services: immich_machine_learning, immich_postgres, immich_redis,
and immich_server are Up and healthy.

Asset size: 390G /mnt/immich/library
Active bind mount: /mnt/immich/library -> /data in immich_server
Database bind mount: /mnt/immich/postgres -> /var/lib/postgresql/data
```

The destination has at least 809G more free space than the total used source
disk. It has enough space for the current 390G asset directory and a database dump.

The backup inventory command returned these existing artifacts:

```text
2025-11-01 17:13 352892036 database.sql
2025-11-01 18:19 182587883308 library.tar.gz
2025-12-30 02:00 141344937 immich-db-backup-20251230T020000-v2.2.1-pg14.19.sql.gz
2026-07-02 10:50 13 library/.immich
2026-07-02 10:50 13 profile/.immich
2026-07-02 10:50 13 upload/.immich
2026-07-02 10:50 179946245 immich-db-upgrade-pre-v3-20260702T104434-0500-v2.7.5.sql.gz
2026-07-02 11:14 249 pre-v3-media-sync-20260702T105121-0500.txt
2026-07-02 11:18 586 v3-upgrade-complete-20260702T111821-0500.txt
```

Warnings:

- The noninteractive SSH session cannot authenticate `sudo`. The privileged
  source-size and service checks did not run.
- The current host has no `/mnt/immich/upload` or `/mnt/immich/profile` path.
  Only `library` is mounted into the Immich server container.
- The external disk is exFAT. It cannot protect `.env` or `system-config.tgz`
  with Unix mode bits. Get explicit approval for physical custody or encryption
  before those files are written.

## Approval gate

Get explicit user approval immediately before the backup commands. State that
the recovery set contains `.env` and host credentials on an exFAT disk. Record
the approved protection method with the final evidence.

## Backup commands

Run these commands on Betty from the Immich deployment directory. Do not print `.env` or secret values.

```bash
cd /home/wcygan/Development/immich-infra
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "/mnt/externalhd/immich-backup/database/$stamp"
set -a; source ./.env; set +a
set -o pipefail
docker compose exec -T database pg_dump -U "$DB_USERNAME" "$DB_DATABASE_NAME" \
  | gzip -n > "/mnt/externalhd/immich-backup/database/$stamp/immich-db.sql.gz"
rsync -a --no-perms --no-owner --no-group --info=progress2 \
  /mnt/immich/library/ /mnt/externalhd/immich-backup/library/
install -m 600 .env "/mnt/externalhd/immich-backup/immich-infra-$stamp.env"
cp docker-compose.yml "/mnt/externalhd/immich-backup/docker-compose-$stamp.yml"
mkdir -p "/mnt/externalhd/immich-backup/betty-host/$stamp"
sudo tar --xattrs --acls -czf \
  "/mnt/externalhd/immich-backup/betty-host/$stamp/system-config.tgz" \
  -C / \
  etc/fstab \
  etc/ssh \
  var/lib/tailscale \
  etc/containers \
  etc/netdata \
  etc/systemd/system \
  home/wcygan/Development/betty/docker-compose.yml \
  home/wcygan/Development/betty/.env \
  var/lib/docker/volumes/betty_netdataconfig/_data
sudo systemctl cat sshd tailscaled docker > "/mnt/externalhd/immich-backup/betty-host/$stamp/service-units.txt"
docker volume ls > "/mnt/externalhd/immich-backup/betty-host/$stamp/docker-volumes.txt"
```

Record the source and destination sizes before copying. Do not use `docker compose down -v`; that removes named volumes.

## Verification commands and expected responses

Run these commands in the same shell as the backup commands. Keep the current
`$stamp` value. The manifest is outside the backup tree, so it cannot hash itself.

```bash
dump="/mnt/externalhd/immich-backup/database/$stamp/immich-db.sql.gz"
gzip -t "$dump" && echo "database archive: OK ($dump)"
test -s "$dump" && echo "database archive: nonempty"
rsync -a -n -c --no-perms --no-owner --no-group --itemize-changes \
  /mnt/immich/library/ /mnt/externalhd/immich-backup/library/
mkdir -p /mnt/externalhd/immich-backup-manifests
manifest="/mnt/externalhd/immich-backup-manifests/SHA256SUMS-$stamp"
find \
  "$dump" \
  /mnt/externalhd/immich-backup/library \
  "/mnt/externalhd/immich-backup/immich-infra-$stamp.env" \
  "/mnt/externalhd/immich-backup/docker-compose-$stamp.yml" \
  "/mnt/externalhd/immich-backup/betty-host/$stamp" \
  -type f -print0 | sort -z | xargs -0 sha256sum > "$manifest"
sha256sum -c "$manifest"
```

Expected responses are `database archive: OK`, `database archive: nonempty`, no
output from the rsync dry run, and a checksum report with no `FAILED` entries.
Preserve the command output with the ticket evidence.

The external disk uses exFAT, so Unix ownership and mode bits are not reliable there. Keep the disk physically controlled and do not expose the `.env` file.

## Completion evidence

The user approved the backup write before it started. The recovery disk is
exFAT. It does not enforce Unix modes. Keep the disk physically controlled.
Encryption at rest was not verified.

The final recovery-set stamp is `20260811T235613Z`.

The final read-only check ran at `2026-08-12T11:09:32Z`.

```text
/mnt/immich:     3.6T total, 391G used, 3.1T free
/mnt/externalhd: 1.9T total, 1.1T used, 739G free
```

The external drive had enough capacity for the 390G active library and the
database dump before the copy. It retained 739G free after the copy.

The current logical database dump is
`/mnt/externalhd/immich-backup/database/20260811T235613Z/immich-db.sql.gz`.
It is 183132192 bytes. `gzip -t` returned zero. The file is nonempty.

The active asset source was `/mnt/immich/library`. The completed rsync copied
417838380605 bytes in 115376 transfers. It took 104 minutes and 49.676 seconds.
The post-copy content comparison returned `parity_exit=0`. It reported one
exFAT timestamp-only difference. It reported no content difference.

The deployment artifacts are on the external drive:

- `immich-infra-20260811T235613Z.env`, 1149 bytes.
- `docker-compose-20260811T235613Z.yml`, 2829 bytes.

The Betty recovery artifacts are in
`/mnt/externalhd/immich-backup/betty-host/20260811T235613Z`:

- `system-config.tgz`, 48436 bytes.
- `service-units.txt`, 5735 bytes.
- `docker-volumes.txt`, 803 bytes.

`tar -tzf system-config.tgz` confirmed SSH configuration, Tailscale state, and
the Netdata Docker-volume configuration are present.

The manifest is
`/mnt/externalhd/immich-backup-manifests/SHA256SUMS-20260811T235613Z`.
The validation ended at `2026-08-12T10:38:24Z` with `checksum_exit=0`.
It checked 158110 entries. It reported 158110 `OK` entries and zero `FAILED`
entries.

Immich remained available while the logical dump and live asset copy ran. This
recovery set is current, but it is not an atomic application snapshot.

## Resources

- [Immich backup and restore](https://docs.immich.app/administration/backup-and-restore/)
- [Docker Compose down](https://docs.docker.com/reference/cli/docker/compose/down/)
