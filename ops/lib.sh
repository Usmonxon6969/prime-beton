# Shared helpers for backup / restore scripts (POSIX sh). Connection comes from PGHOST/PGUSER/PGPASSWORD/PGDATABASE.
BACKUP_DIR="${BACKUP_DIR:-/backups}"
PREFIX="prime-beton"

# decrypt_to_stdout FILE  -> plain .sql on stdout (handles .sql.gz and .sql.gz.enc)
dump_stream() {
  f="$1"
  case "$f" in
    *.enc)
      [ -n "$BACKUP_PASSPHRASE" ] || { echo "BACKUP_PASSPHRASE is needed to read $f" >&2; return 2; }
      openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:BACKUP_PASSPHRASE -in "$f" | gunzip ;;
    *) gunzip -c "$f" ;;
  esac
}

latest_backup() {
  ls -1t "$BACKUP_DIR"/${PREFIX}-*.sql.gz "$BACKUP_DIR"/${PREFIX}-*.sql.gz.enc "$BACKUP_DIR"/prime-stroy-*.sql.gz 2>/dev/null | head -n 1
}
