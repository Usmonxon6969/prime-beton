# Security and data safety

## What the system already does
- Passwords are stored only as salted **scrypt** hashes. Logins are rate-limited (too many attempts are refused for a while).
- Every request needs a signed token (12 h). Each role sees and changes only its own sections; this is enforced **on the server**, not only in the screens.
- The **change journal** records who created, changed, deleted or restored what. Deleted documents are kept (marked deleted) and can be restored.
- The database is not published to the network: only the app (port 8000) is reachable. API answers are sent with `Cache-Control: no-store` and basic browser protection headers.
- AI: the API keys stay on the server. The AI reads only what the signed-in role may open and cannot change data.

## Before real use (checklist)
1. `.env`: long random `SECRET_KEY` (`openssl rand -hex 32`), strong `POSTGRES_PASSWORD` and `ADMIN_PASSWORD`, `SEED_DEMO_USERS=false`. Never commit or share `.env`.
2. **HTTPS.** The app speaks plain HTTP: turn on the built-in Caddy (see *HTTPS* below) and do not expose port 8000 to the internet directly.
   Also: `BACKUP_PASSPHRASE` (encrypted backups) and, for the management roles, `REQUIRE_2FA_ROLES`.
3. Give each person their own login and the lowest role that lets them work. Disable users who leave (Users screen).
4. Keep the server updated and restrict who can log in to the machine.

## Sign-in protection
- **Password rules** (everyone, enforced by the server): at least 10 characters, with a letter and a digit, not a common password, and it must not contain the username.
- **Two-factor login (2FA).** Each person can turn it on in *Security*: scan the QR code with Google Authenticator, Microsoft Authenticator, Authy or 1Password, type the 6-digit code once, done. From then on the code is asked after the password. A code works only once. The secret is stored encrypted on the server.
  - Lost phone? An administrator opens *Users* and presses **Reset 2FA** for that person; they sign in with the password and set it up again.
  - To **require** it for some roles, set in `.env`: `REQUIRE_2FA_ROLES=admin,direktor`. Those users can only open the Security page until 2FA is on.
- **Signed-in browsers.** *Security* lists every browser that is signed in (device, address, last activity). Each can be signed out remotely, or "sign out all others". Changing or resetting a password signs out all other browsers automatically. *Sign out* ends the session on the server too (a stolen token stops working at once).

## Backups
`docker compose up -d` also starts a `backup` container: a dump every 24 hours into `./backups` (the last 14 days are kept; change with `BACKUP_EVERY_HOURS`, `BACKUP_KEEP_DAYS`).

**Every backup is test-restored right after it is made.** The container loads it into a throw-away database, compares every table and its row count with the live database, and deletes the test database. The verdict is in `backups/last-restore-check.txt` (starts with `OK`). If a backup cannot be made or does not restore, `backups/BACKUP_FAILED.txt` appears - check for that file (or for the absence of a fresh `last-restore-check.txt`) from time to time.

Check by hand at any time: `docker compose exec backup sh /ops/restore-check.sh`

**Encrypted backups.** Put a long passphrase into `.env`: `BACKUP_PASSPHRASE=...`. New backups are then AES-256 encrypted (`*.sql.gz.enc`) and are unreadable without it. **Keep the passphrase in a safe place that is NOT this server** - without it the backups cannot be opened, by anybody. Old plain backups stay as they are until they expire.

Copy the `backups` folder off the machine regularly (another disk, cloud storage): a backup on the same disk does not survive a broken disk.

**Off-site copy.** With the Telegram bot running, every verified (test-restored) *encrypted* backup is also sent, silently, to the Telegram chat of the main administrator (the owner account) ONLY - no other admin or user ever receives it. The owner must open the bot and link their account once; until then nothing is sent. Plain (unencrypted) dumps are never sent. Files above ~48 MB are not uploaded; the admin gets a notice instead. Switch off with `TELEGRAM_SEND_BACKUPS=false`. By default a backup is made every 6 hours (`BACKUP_EVERY_HOURS`).

Manual backup now: `docker compose exec backup sh /ops/backup.sh once`

**Restore** (this replaces the current data):
```
docker compose stop api
docker compose exec backup sh /ops/restore.sh /backups/FILE_NAME --yes
docker compose start api
```
(`FILE_NAME` is e.g. `prime-beton-20261013-020000.sql.gz.enc`. Older `prime-stroy-*.sql.gz` files restore the same way.)

## HTTPS
Without HTTPS passwords and codes cross the network unprotected, so use it as soon as the system is reachable from outside the office.
1. Point a domain (DNS A record) to the server; open ports 80 and 443.
2. In `.env`: `DOMAIN=erp.yourcompany.uz`, `API_BIND=127.0.0.1`, `FORWARDED_ALLOW_IPS=*`.
3. `docker compose --profile https up -d`. Caddy gets and renews the certificate by itself. The app is then reachable only through `https://` (port 8000 is closed to the outside).

## Load test
`ops/loadtest.py` fills a *test* copy with thousands of documents through the real API and times every screen (run it only against a throw-away database, never your real one).
Result with 4 000 orders, 2 700 delivery notes, 2 000 payments, 570 receipts on PostgreSQL 16 (one laptop-class machine): every one of 24 screens opens in under 0.6 s; creating documents ~29 per second with 6 parallel users. The test found and fixed two real faults: parallel first documents of a series could fail with a server error, and the order list, dashboard and production plan asked the database once per order (6 s at 4 000 orders, now 0.4-0.6 s).
Note: lists load the whole chosen period; keep the period filter (month/quarter) on the busiest screens when you have tens of thousands of documents.

## What deletes data
Only `docker compose down -v`, `docker volume rm prime-stroy_dbdata`, Docker Desktop *Clean up / Prune*, `python -m app.tools.reset_data --yes` (wipes everything) and `python -m app.tools.clear_movements --yes` (only the test movements; see below). Restart, stop, `up`, `up --build` never delete data.

## Not included (be aware)
Encryption of the server disk itself (use the operating system's disk encryption), and monitoring/alerting of the server. Add them at the server level if your policy requires it.


## Telegram bot (ixtiyoriy)
- Token @BotFather'dan olinadi va **faqat serverdagi `.env`** ga yoziladi (`TELEGRAM_BOT_TOKEN`). U brauzerga, jurnalga yoki zip'ga tushmaydi (bot so‘rov URL'larini jurnalga yozmaydi, chunki token URL ichida).
- Ishga tushirish: `docker compose --profile telegram up -d`. Bot faqat Telegram'ga **chiqish** so‘rovlarini yuboradi; internetga port ochilmaydi.
- Ulash: foydalanuvchi veb-ilovada «Xavfsizlik → Telegram → Ulash kodini olish» bosadi, botga `/start KOD` yuboradi. Kod 8 belgi, 10 daqiqa, bir marta ishlaydi (bazada faqat hash). 5 ta xato urinishdan keyin chat 10 daqiqaga bloklanadi.
- Bot faqat shaxsiy chatlarda javob beradi (guruh va kanallar e’tiborsiz). Har bir buyruq foydalanuvchining roli bo‘yicha cheklanadi; o‘chirilgan foydalanuvchi darhol uziladi. Ulash/uzish o‘zgarishlar jurnaliga yoziladi.
- Buyruqlar: /brief, /stock nom, /debts, /cash, /alerts on|off, /lang uz|ru|en, /unlink. Avto-xabarlar: yangi jiddiy signallar (har biri 3 kunda bir marta).
- Eslatma: Telegram xabarlari Telegram serverlari orqali o‘tadi. Juda maxfiy raqamlar kerak bo‘lmasa, rol cheklovlarini (masalan, faqat direktor) saqlang.

## Handing over to the client: clear the test movements
`docker compose exec backup sh /ops/backup.sh once` first, then `docker compose exec api python -m app.tools.clear_movements` shows what would be deleted (nothing changes). Add `--yes` to delete.
Deleted: orders, delivery notes, receipts, production, stock counts and write-offs, all cash and bank movements, worker pay adjustments, stock balances and history, the journal entries of those documents, the document number counters (numbering restarts at 1) and the bot's memory of announced documents.
Kept: products, materials, specifications, piece rates, units, warehouses and plants, money accounts (with their opening balances), customers, suppliers, workers, users, company details and Telegram links.

## Main administrator and getting back in

The first administrator is the **main administrator**: other users do not see this account in Users and cannot change it
(password, role, activity, authenticator). Its actions stay in the change journal under its name.

If its password or authenticator is lost, nobody needs to be asked: whoever can open a shell on the server can restore access.

    cd ~/prime-beton
    docker compose exec api python -m app.tools.reset_owner                # asks for a new password (typed twice, not shown)
    docker compose exec api python -m app.tools.reset_owner --generate     # or makes a strong one and shows it once
    docker compose exec api python -m app.tools.reset_owner --reset-2fa    # also turns the authenticator code off

The account is reactivated and signed out everywhere; the recovery is written to the change journal. Keep the password and the
backup passphrase together, away from the server (a password manager). Whoever has root on the server can always do this, so
protect the server login (SSH key, no password sign-in).
