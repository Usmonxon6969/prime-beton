#!/bin/sh
# Proves that a backup can really be restored: loads it into a throw-away database on the same server,
# compares tables and row counts with the live database, then drops the throw-away database.
#   restore-check.sh [FILE]     (default: the newest file in BACKUP_DIR)
# Exit 0 = the backup restores and matches. Writes the verdict to $BACKUP_DIR/last-restore-check.txt.
. "$(dirname "$0")/lib.sh"
f="${1:-$(latest_backup)}"
[ -n "$f" ] && [ -f "$f" ] || { echo "no backup file found in $BACKUP_DIR" >&2; exit 2; }
LIVE="${PGDATABASE:-daybook}"
TMP="restorecheck_$(date +%s)"
report="$BACKUP_DIR/last-restore-check.txt"
fail() { echo "RESTORE CHECK FAILED: $1" | tee "$report" >&2; psql -qAt -d postgres -c "DROP DATABASE IF EXISTS $TMP" >/dev/null 2>&1; exit 1; }

SQL="$BACKUP_DIR/.check-$$.sql"; trap 'rm -f "$SQL" "$BACKUP_DIR/.restore-err"' EXIT
dump_stream "$f" >"$SQL" 2>"$BACKUP_DIR/.restore-err" || fail "cannot read the file (wrong BACKUP_PASSPHRASE or damaged file)"
[ -s "$SQL" ] && grep -q "PostgreSQL database dump" "$SQL" || fail "the file is empty or is not a database dump"
psql -qAt -d postgres -c "CREATE DATABASE $TMP" >/dev/null || fail "cannot create the test database"
psql -q -v ON_ERROR_STOP=1 -d "$TMP" -f "$SQL" >/dev/null 2>"$BACKUP_DIR/.restore-err" || fail "the dump does not load: $(head -c 300 "$BACKUP_DIR/.restore-err")"

# every table: restored row count vs live row count
tables="$(psql -qAt -d "$LIVE" -c "select tablename from pg_tables where schemaname='public' order by 1")"
[ -n "$tables" ] || fail "the live database has no tables"
lines=""; total=0
for t in $tables; do
  live="$(psql -qAt -d "$LIVE" -c "select count(*) from \"$t\"")"
  back="$(psql -qAt -d "$TMP" -c "select count(*) from \"$t\"" 2>/dev/null)" || fail "table $t is missing in the backup"
  [ "$live" -gt 0 ] && [ "$back" -eq 0 ] && fail "table $t has $live rows now but 0 in the backup"
  [ "$back" -gt "$live" ] && lines="$lines\n  note: $t has fewer rows now ($live) than in the backup ($back) - rows were removed after it"
  total=$((total + back))
done
v_live="$(psql -qAt -d "$LIVE" -c "select version_num from alembic_version" 2>/dev/null)"
v_back="$(psql -qAt -d "$TMP" -c "select version_num from alembic_version" 2>/dev/null)"
[ "$v_live" = "$v_back" ] || fail "schema version differs (backup $v_back, live $v_live)"
psql -qAt -d postgres -c "DROP DATABASE $TMP" >/dev/null
printf "OK %s\n  file: %s\n  tables: %s, rows restored: %s, schema version: %s%b\n" "$(date -Iseconds)" "$(basename "$f")" "$(echo "$tables" | wc -l | tr -d ' ')" "$total" "$v_back" "$lines" | tee "$report"
