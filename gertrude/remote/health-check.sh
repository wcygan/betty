#!/bin/sh
# Managed by gertrude/manage.py. Counters are ephemeral; samples persist on disk.
set -eu
. "${GERTRUDE_CONFIG:-/etc/gertrude-health.conf}"
proc=${GERTRUDE_PROC:-/proc}
state=${GERTRUDE_STATE:-/run/gertrude-health}
history=${GERTRUDE_HISTORY:-/var/lib/gertrude-health/history}
mkdir -p "$state"
exec 9>"$state/lock"
flock -n 9 || exit 0
tmp=$(mktemp "$state/sample.XXXXXX")
trap 'rm -f "$tmp"' EXIT HUP INT TERM
now=$(date +%s)
old_time=0
old_oom=0
old_in=0
old_out=0
low_count=0
pressure_count=0
old_incidents=unknown
old_prune=none
# This file is written only by this root-owned service in its root-owned directory.
if [ -f "$state/counters" ]; then . "$state/counters"; fi
available=$(awk '/^MemAvailable:/ {print int($2/1024)}' "$proc/meminfo")
[ -n "$available" ] || { echo 'MemAvailable unavailable' >&2; exit 1; }
swap_free=$(awk '/^SwapFree:/ {print int($2/1024)}' "$proc/meminfo")
oom=$(awk '$1=="oom_kill" {print $2}' "$proc/vmstat")
swap_in=$(awk '$1=="pswpin" {print $2}' "$proc/vmstat")
swap_out=$(awk '$1=="pswpout" {print $2}' "$proc/vmstat")
pressure=unavailable
if [ -r "$proc/pressure/memory" ]; then
  pressure=$(awk '/^full / {split($3,a,"="); print a[2]}' "$proc/pressure/memory")
  pressure=${pressure:-unavailable}
fi
incidents=
if [ "$available" -lt "$MIN_AVAILABLE_MIB" ]; then low_count=$((low_count+1)); else low_count=0; fi
if [ "$pressure" != unavailable ] && awk -v p="$pressure" -v t="$PRESSURE_FULL_PERCENT" 'BEGIN {exit !(p>t)}'; then
  pressure_count=$((pressure_count+1))
else pressure_count=0; fi
[ "$low_count" -lt "$CONSECUTIVE_SAMPLES" ] || incidents="${incidents}low-memory,"
[ "$pressure_count" -lt "$CONSECUTIVE_SAMPLES" ] || incidents="${incidents}memory-pressure,"
oom_delta=unavailable
if [ -n "$oom" ]; then
  oom_delta=0
  if [ "$old_time" -gt 0 ] && [ "$oom" -ge "$old_oom" ]; then oom_delta=$((oom-old_oom)); fi
  [ "$oom_delta" -eq 0 ] || incidents="${incidents}oom-kill,"
fi
{
  echo "timestamp=$now"
  echo "boot_id=$(cat "$proc/sys/kernel/random/boot_id")"
  echo "available_mib=$available"
  echo "swap_free_mib=$swap_free"
  echo "memory_full_avg60=$pressure"
  echo "oom_kills_since_boot=${oom:-unavailable}"
  echo "oom_kills_since_sample=$oom_delta"
  if [ "$old_time" -gt 0 ] && [ "$now" -gt "$old_time" ]; then
    echo "sample_seconds=$((now-old_time))"
    echo "swap_in_pages=$((swap_in-old_in))"
    echo "swap_out_pages=$((swap_out-old_out))"
  fi
  for path in / /nix; do
    disk=$(df -P "$path" | awk 'END {gsub(/%/,"",$5);print 100-$5}')
    inode=$(df -Pi "$path" | awk 'END {gsub(/%/,"",$5);print 100-$5}')
    echo "disk_free_percent[$path]=$disk"
    echo "inode_free_percent[$path]=$inode"
    [ "$disk" -ge "$MIN_DISK_FREE_PERCENT" ] || incidents="${incidents}disk:$path,"
    [ "$inode" -ge "$MIN_DISK_FREE_PERCENT" ] || incidents="${incidents}inodes:$path,"
  done
  for service in $SERVICES; do
    active=$(systemctl is-active "$service" 2>/dev/null || true)
    echo "service[$service]=$active"
    [ "$active" = active ] || incidents="${incidents}service:$service,"
  done
  incidents=${incidents:-healthy}
  echo "incidents=$incidents"
} > "$tmp"
# Keep today and the preceding RETENTION_DAYS-1 UTC dates. Prune on the first
# successful sample each day (and after a reboot), under the sampler lock.
umask 027
if [ ! -d "$history" ]; then
  mkdir -p "$history"
  # Persist the new directory entries as well as subsequent file contents.
  parent=$(dirname "$history")
  sync "$history" "$parent" "$(dirname "$parent")"
fi
day=$(date -u -d "@$now" +%Y%m%d)
if [ "$old_prune" != "$day:$RETENTION_DAYS" ]; then
  cutoff=$(date -u -d "@$(( (now / 86400 - RETENTION_DAYS + 1) * 86400 ))" +%Y%m%d)
  for file in "$history"/*.samples; do
    [ -f "$file" ] && [ ! -L "$file" ] || continue
    name=${file##*/}
    case "$name" in
      [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].samples)
        [ "${name%.samples}" -ge "$cutoff" ] || rm -- "$file" ;;
    esac
  done
fi
file="$history/$day.samples"
[ ! -L "$file" ] || { echo 'Refusing history symlink' >&2; exit 1; }
# A leading newline separates any torn tail left by an interrupted append.
# The reader requires the version prefix and end marker to accept a record.
record=$(awk 'BEGIN {ORS=""} {if (NR>1) printf "\t"; printf "%s", $0}' "$tmp")
printf '\nv1\t%s\tend\n' "$record" >> "$file"
# GNU sync with named paths fsyncs just the file and directory, not the disk.
# Publish the fresh status only after durable history succeeds.
sync "$file" "$history"
old_prune="$day:$RETENTION_DAYS"
chmod 644 "$tmp"
mv "$tmp" "$state/status"
if [ "$incidents" != "$old_incidents" ]; then echo "health transition: $old_incidents -> $incidents"; fi
# Atomic replacement; values are numeric or validated service-derived labels.
tmp=$(mktemp "$state/counters.XXXXXX")
{
  echo "old_prune=$old_prune"
  echo "old_time=$now"
  echo "old_oom=${oom:-0}"
  echo "old_in=$swap_in"
  echo "old_out=$swap_out"
  echo "low_count=$low_count"
  echo "pressure_count=$pressure_count"
  echo "old_incidents='$incidents'"
} > "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$state/counters"
