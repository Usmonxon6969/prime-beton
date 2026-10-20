# Prime Beton — topshirish hujjati

## 1. Tizim nima qiladi
Temir-beton zavodi uchun yagona tizim: ishlab chiqarish, ombor, sotuv, xaridlar, pul (bank/kassa), hisobotlar va AI yordamchi. Uch tilda: o‘zbek, rus, ingliz. Veb-ilova: serverga o‘rnatiladi, foydalanuvchilar brauzerdan ishlaydi.

## 2. Topshiriladigan narsalar
- To‘liq dastur kodi (`backend/`, `frontend/`), Docker sozlamalari (`docker-compose.yml`, `.env.example`).
- Hujjatlar: `README.md` (o‘rnatish), `docs/user-guide-uz.md` (foydalanuvchi qo‘llanmasi), `docs/security.md` (xavfsizlik va zaxira), `docs/ai.md` (AI), `docs/architecture.md` (dasturchilar uchun).
- Avtomatik testlar (91 ta) va brauzer testlari (`e2e/`).

## 3. O‘rnatish (qisqacha)
1. Docker o‘rnatilgan serverda papkani oching, `cp .env.example .env`.
2. `.env` da o‘zgartiring: `POSTGRES_PASSWORD`, `SECRET_KEY` (`openssl rand -hex 32`), `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SEED_DEMO_USERS=false`; AI uchun `ANTHROPIC_API_KEY` yoki `GEMINI_API_KEY`.
3. `docker compose up -d --build`, so‘ng http://SERVER:8000 (haqiqiy ishda HTTPS orqasida, `docs/security.md`).
4. Administrator bilan kiring va quyidagilarni kiriting: zavodlar va omborlar (Sozlamalar), materiallar, mahsulotlar va spetsifikatsiyalar, bank/kassa hisoblari va boshlang‘ich qoldiqlar, foydalanuvchilar.

## 4. Qabul qilish tekshiruvi (topshirishda birga o‘tkazing)
| # | Tekshiruv | Natija kutilgani |
|---|-----------|------------------|
| 1 | Administrator bilan kirish, noto‘g‘ri parol bilan kira olmaslik | kirish faqat to‘g‘ri parol bilan |
| 2 | Zavod va ombor yaratish (Sozlamalar → Omborlar) | ro‘yxatda turi bilan ko‘rinadi |
| 3 | Material, mahsulot va spetsifikatsiya kiritish | Ombor sahifasida paydo bo‘ladi |
| 4 | Kirim nakladnoyi | qoldiq oshadi, raqam `PN-…` |
| 5 | Ishlab chiqarish hujjati | xomashyo normadan kamayadi, tayyor mahsulot qo‘shiladi |
| 6 | Qoldiqdan ortiq chiqim | tizim rad etadi («yetarli emas») |
| 7 | Buyurtma va chiqim nakladnoyi, PDF | to‘g‘ri summa, PDF ochiladi |
| 8 | To‘lov (bank/kassa) va akt sverka | mijoz qarzi to‘g‘ri hisoblanadi |
| 9 | Bir nechta hujjatni yorliqlarda ochish | ma‘lumot yo‘qolmaydi |
| 10 | Har rol bilan kirish (omborchi, sotuv, buxgalter) | faqat o‘z bo‘limlarini ko‘radi |
| 11 | AI yordamchi va AI orqali hujjat kiritish | kalit kiritilgach javob beradi, qoralama tekshirib yaratiladi |
| 12 | `docker compose restart` dan keyin ma‘lumot joyida | ma‘lumot saqlanadi; `./backups` da zaxira fayl bor |

## 5. Bu paketda tekshirilgan
Toza o‘rnatishda (bo‘sh baza): kirish, noto‘g‘ri parolni rad etish, demo loginlar yo‘qligi, zavod/ombor/material/mahsulot yaratish, kirim, ishlab chiqarish, chiqim, qoldiqning to‘g‘ri hisoblanishi, ortiqcha chiqimni rad etish. 103 avtomatik test (shu jumladan haqiqiy PostgreSQL 16 ustida) va brauzer oqimlari o‘tgan. Migratsiyalar (`alembic upgrade head`) Postgres’da tekshirilgan; 4000 buyurtmali yuklama sinovida barcha ekranlar 0.6 s dan tez.

## 6. Topshirishdan oldin MIJOZ MUHITIDA tekshirilishi shart (men tekshira olmaganlarim)
- **Docker bilan o‘rnatish, zaxira konteyneri va Caddy (HTTPS)** Docker’ning o‘zida sinalmagan (zaxira/tiklash skriptlari esa haqiqiy Postgres’da sinalgan): birinchi ishga tushirishda `./backups/last-restore-check.txt` fayli `OK` bilan paydo bo‘lishini tekshiring (`docs/security.md`).
- **Haqiqiy AI**: Claude/Gemini bilan hech qachon ishlatib ko‘rilmagan (faqat sinov javoblari bilan). Kalit kiritilgach 11-bandni sinang; model nomi o‘zgargan bo‘lsa `.env` da `AI_MODEL` / `GEMINI_MODEL` ni almashtiring.
- **PDF ko‘rinishi** haqiqiy Chrome’da ko‘rib chiqilishi kerak.
- **HTTPS**: domen va 80/443 portlar kerak; `docs/security.md` dagi «HTTPS» bo‘limi.

## 7. Ma‘lum cheklovlar
- Pul to‘lovlari AI qoralamasidan to‘g‘ridan-to‘g‘ri yaratilmaydi (pul shaklida ochiladi).
- Yorliqlar sahifa yangilanganda (F5) saqlanmaydi.
- Narx ro‘yxatlari, chegirmalar va ish haqi moduli hali yo‘q.

## 8. Qo‘llab-quvvatlash
Xatolik bo‘lsa: `docker compose logs api` natijasi va nima bosilgani haqida ma‘lumot yuboring.
