#!/bin/sh
# Restore a backup INTO THE LIVE DATABASE (replaces its data). Stop the api first.
#   restore.sh FILE --yes
. "$(dirname "$0")/lib.sh"
f="$1"; [ -f "$f" ] || { echo "usage: restore.sh BACKUP_FILE --yes" >&2; exit 2; }
[ "$2" = "--yes" ] || { echo "This REPLACES the current data of '${PGDATABASE:-daybook}'. Run again with --yes to confirm." >&2; exit 2; }
db="${PGDATABASE:-daybook}"
SQL="$BACKUP_DIR/.restore-$$.sql"; trap 'rm -f "$SQL"' EXIT
dump_stream "$f" >"$SQL" || { echo "cannot read the file (wrong BACKUP_PASSPHRASE or damaged file) - nothing was changed" >&2; exit 1; }
grep -q "PostgreSQL database dump" "$SQL" || { echo "not a database dump - nothing was changed" >&2; exit 1; }
psql -q -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$db' AND pid<>pg_backend_pid()" >/dev/null
psql -q -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE $db" -c "CREATE DATABASE $db" || exit 1
psql -q -v ON_ERROR_STOP=1 -d "$db" -f "$SQL" >/dev/null && echo "restored from $f"
