# 01 — Create and validate upgrade recovery backup

**What to build:** A current, restorable recovery set for Betty before any operating system change.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Create a current Immich PostgreSQL dump while the database is available.
- [ ] Back up the Immich asset folders and the deployment configuration.
- [ ] Back up Betty configuration and service definitions needed to restore SSH, Tailscale, Docker, and Netdata.
- [ ] Store the recovery set on the external backup drive.
- [ ] Verify archive integrity and record backup timestamps and sizes.
- [ ] Confirm the backup includes both Immich metadata and asset files, not image files alone.

## Current Betty locations

- Immich deployment: `/home/wcygan/Development/immich-infra`.
- Immich source data: `/mnt/immich` on the `immich-primary` ext4 disk.
- Existing backup disk: `/mnt/externalhd` on the `externalhdd` exFAT disk.
- Existing backup roots: `/mnt/externalhd/immich-backup` and `/mnt/externalhd/immich-backups`.

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
ssh betty 'sudo du -sh /mnt/immich/library /mnt/immich/upload /mnt/immich/profile /mnt/immich/postgres'
ssh betty 'find /mnt/externalhd/immich-backup /mnt/externalhd/immich-backups -maxdepth 2 -type f -printf "%TY-%Tm-%Td %TH:%TM %s %p\\n" | sort'
```

Expected evidence includes both mounts, enough free space for the measured source data, four running Immich containers, and dated backup files.

The last observation had this shape; do not treat it as a current measurement:

```text
/dev/sdb2  3.6T  391G  3.1T  12%  /mnt/immich
/dev/sda2  1.9T  718G  1.2T  38%  /mnt/externalhd
```

## Backup commands

Run these commands on Betty from the Immich deployment directory. Do not print `.env` or secret values.

```bash
cd /home/wcygan/Development/immich-infra
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "/mnt/externalhd/immich-backup/database/$stamp"
set -a; source ./.env; set +a
docker compose exec -T database pg_dump -U "$DB_USERNAME" "$DB_DATABASE_NAME" \
  | gzip -n > "/mnt/externalhd/immich-backup/database/$stamp/immich-db.sql.gz"
rsync -a --info=progress2 /mnt/immich/library/ /mnt/externalhd/immich-backup/library/
rsync -a --info=progress2 /mnt/immich/upload/ /mnt/externalhd/immich-backup/upload/
rsync -a --info=progress2 /mnt/immich/profile/ /mnt/externalhd/immich-backup/profile/
install -m 600 .env "/mnt/externalhd/immich-backup/immich-infra-$stamp.env"
cp docker-compose.yml "/mnt/externalhd/immich-backup/docker-compose-$stamp.yml"
mkdir -p "/mnt/externalhd/immich-backup/betty-host/$stamp"
sudo tar --xattrs --acls --ignore-failed-read -czf \
  "/mnt/externalhd/immich-backup/betty-host/$stamp/system-config.tgz" \
  /etc/fstab /etc/ssh /etc/tailscale /etc/docker /etc/systemd/system
sudo systemctl cat sshd tailscaled docker > "/mnt/externalhd/immich-backup/betty-host/$stamp/service-units.txt"
docker volume ls > "/mnt/externalhd/immich-backup/betty-host/$stamp/docker-volumes.txt"
```

Record the source and destination sizes before copying. Do not use `docker compose down -v`; that removes named volumes.

## Verification commands and expected responses

```bash
verify_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dump="$(find /mnt/externalhd/immich-backup/database -type f -name 'immich-db.sql.gz' -printf '%T@ %p\\n' | sort -nr | head -n 1 | cut -d' ' -f2-)"
gzip -t "$dump" && echo "database archive: OK ($dump)"
find /mnt/externalhd/immich-backup -type f -print0 | sort -z | xargs -0 sha256sum > "/mnt/externalhd/immich-backup/SHA256SUMS-$verify_stamp"
sha256sum -c "/mnt/externalhd/immich-backup/SHA256SUMS-$verify_stamp" | tail -n 1
```

Expected responses are `database archive: OK` and a checksum summary with no `FAILED` entries. Preserve the command output with the ticket evidence.

The external disk uses exFAT, so Unix ownership and mode bits are not reliable there. Keep the disk physically controlled and do not expose the `.env` file.

## Resources

- [Immich backup and restore](https://docs.immich.app/administration/backup-and-restore/)
- [Docker Compose down](https://docs.docker.com/reference/cli/docker/compose/down/)
