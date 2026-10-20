#!/bin/sh
# Prime Beton database backup.
#   backup.sh once   - one dump now, then verify it (restore into a throw-away database)
#   backup.sh        - dump every BACKUP_EVERY_HOURS (default 24) forever (what the "backup" container runs)
# BACKUP_PASSPHRASE set  -> files are AES-256 encrypted (.sql.gz.enc); empty -> plain .sql.gz
# Keeps the last BACKUP_KEEP_DAYS (default 14) days. On any failure writes BACKUP_FAILED.txt next to the backups.
. "$(dirname "$0")/lib.sh"
KEEP="${BACKUP_KEEP_DAYS:-14}"
EVERY="${BACKUP_EVERY_HOURS:-24}"

one() {
  ts="$(date +%Y%m%d-%H%M%S)"
  ext="sql.gz"; [ -n "$BACKUP_PASSPHRASE" ] && ext="sql.gz.enc"
  out="$BACKUP_DIR/$PREFIX-$ts.$ext"
  mkdir -p "$BACKUP_DIR"
  # pg_dump | gzip [| openssl]; the shell has no pipefail, so the exit codes are collected through a status file
  st="$BACKUP_DIR/.st.$$"; rm -f "$st"
  if [ -n "$BACKUP_PASSPHRASE" ]; then
    { pg_dump --no-owner --no-privileges || echo 1 >"$st"; } | gzip | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:BACKUP_PASSPHRASE -out "$out.tmp" || echo 1 >"$st"
  else
    { pg_dump --no-owner --no-privileges || echo 1 >"$st"; } | gzip >"$out.tmp" || echo 1 >"$st"
  fi
  if [ -e "$st" ] || [ ! -s "$out.tmp" ]; then rm -f "$out.tmp" "$st"; return 1; fi
  mv "$out.tmp" "$out"; chmod 600 "$out"
  echo "backup written: $out ($(wc -c <"$out") bytes)"
  "$(dirname "$0")/restore-check.sh" "$out" || return 1
  find "$BACKUP_DIR" \( -name "$PREFIX-*.sql.gz" -o -name "$PREFIX-*.sql.gz.enc" -o -name "prime-stroy-*.sql.gz" \) -mtime +"$KEEP" -delete
  return 0
}

run() {
  if one; then rm -f "$BACKUP_DIR/BACKUP_FAILED.txt"
  else echo "$(date -Iseconds) backup or its verification FAILED - see the backup container log" >"$BACKUP_DIR/BACKUP_FAILED.txt"; return 1; fi
}

if [ "$1" = "once" ]; then run; exit $?; fi
while true; do run; sleep $((EVERY * 3600)); done
