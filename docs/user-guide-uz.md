# Prime Beton — foydalanuvchi qo‘llanmasi

## Kirish va rollar
Login va parolni administrator beradi. Har kim faqat o‘z rolidagi bo‘limlarni ko‘radi:
- **Administrator / direktor** — hammasi, shu jumladan o‘zgarishlar jurnali va foydalanuvchilar.
- **Ishlab chiqarish boshlig‘i** — ishlab chiqarish, spetsifikatsiyalar, materiallar, mahsulotlar.
- **Omborchi** — ombor, kirim va chiqim nakladnoylari.
- **Sotuv menejeri** — mijozlar, buyurtmalar, chiqim nakladnoylari.
- **Buxgalter** — bank, kassa, to‘lovlar, hisobotlar, akt sverka.

Til (UZ / RU / EN) va qorong‘i rejim tepa o‘ng burchakda.

## Xavfsizlik (parol, 2FA, kirgan brauzerlar)
Chap menyudagi **Xavfsizlik** bo‘limi:
- **Parol** kamida 10 belgi, harf va raqam bilan; oson parollar (`password123` kabi) va login o‘zi qabul qilinmaydi.
- **Ikki bosqichli kirish (2FA)**: telefondagi Google/Microsoft Authenticator (yoki Authy, 1Password) bilan QR-kodni skanerlang, 6 xonali kodni kiriting. Keyin paroldan so‘ng har safar kod so‘raladi (har bir kod faqat bir marta ishlaydi).
- Telefon yo‘qolsa: administrator **Foydalanuvchilar** bo‘limida «2FA ni tiklash» tugmasini bosadi, siz paroldan kirib qaytadan ulaysiz.
- **Kirgan brauzerlar** ro‘yxati: begona qurilma ko‘rsangiz, uni uzib qo‘ying yoki «boshqalarni uzish» ni bosing. Parol almashtirilganda boshqa brauzerlar o‘zi uziladi.

## Birinchi sozlash (administrator)
1. **Sozlamalar → Omborlar → Yaratish**: zavodlar (ishlab chiqarish joyi) va omborlarni «Turi» bilan kiriting.
2. **Materiallar** va **Mahsulotlar**ni kiriting, **Spetsifikatsiyalar**da har mahsulotga xomashyo normasini yozing (normasiz mahsulot ham ishlab chiqarilishi mumkin, u xomashyo sarflamaydi).
3. **Sozlamalar → Bank hisoblari / Kassalar**: hisoblar va boshlang‘ich qoldiq.
4. **Foydalanuvchilar**: har xodimga alohida login va mos rol.

## Kundalik ish
**Kirim (xarid):** Kirim nakladnoylari → Yaratish → yetkazib beruvchi, ombor, material, miqdor, narx → O‘tkazish. Yetkazib beruvchi yo‘q bo‘lsa «+ Yangi yetkazib beruvchi» ni bosing.
**Ishlab chiqarish:** Ishlab chiqarish → Yaratish → zavod, mahsulot, miqdor → «Spetsifikatsiya bo‘yicha to‘ldirish» xomashyo sarfini ko‘rsatadi → O‘tkazish va yopish. Xomashyo yetmasa tizim aytadi.
**Buyurtma va chiqim:** Buyurtmalar → Yaratish (mijoz «+ Yangi mijoz» bilan shu yerda qo‘shiladi) → buyurtmadan chiqim nakladnoyi yarating. Qoldiqdan ortiq chiqim bo‘lmaydi. Chiqim nakladnoyini PDF qilib oching.
**Pul:** Bank yoki Kassa → Yaratish: kirim, chiqim yoki o‘tkazma. Mijoz/yetkazib beruvchi qarzi avtomatik hisoblanadi.
**Akt sverka:** Mijozlar (yoki Yetkazib beruvchilar) → ⋮ → Akt sverka → davrni tanlang → PDF.

## Bir nechta hujjat bilan ishlash
Har ochiq hujjat sahifa tepasida yorliq bo‘ladi. Boshqa hujjatga o‘tsangiz, to‘ldirilgani saqlanib turadi. Sariq nuqta — saqlanmagan. Yopish uchun × ni ikki marta bosing. Saqlangan hujjatning yorlig‘i o‘zi yopiladi.

## AI yordamchi
- **Savol berish:** «Armatura qancha qoldi?», «Kim bizga qarz?». AI faqat sizning huquqingizdagi ma‘lumotni o‘qiydi va hech narsani o‘zgartirmaydi.
- **Hujjatni AI bilan kiritish:** matn yoki nakladnoy rasmini bering (lotin, kirill va xatolar bo‘lsa ham tushunadi) → qoralamani tekshiring: hamkor, ombor, har qatordagi mahsulot va miqdor → «Hujjatni yaratish». Topilmagan yoki o‘xshash nomlarni o‘zingiz tanlaysiz. Kirim, chiqim, buyurtma va ishlab chiqarish shu yo‘l bilan kiritiladi.
- Har doim yaratishdan oldin raqamlarni tekshiring: AI xato qilishi mumkin.

## Hisobotlar
Hisobotlar bo‘limida: oborot qaydnomasi, sotuv, xaridlar, pul oqimi, foyda (taxminiy), ishlab chiqarish rejasi, xomashyo yetishmasligi, mijoz va yetkazib beruvchi qarzlari. Hammasini Excel’ga yuklash mumkin.

## Inventarizatsiya va hisobdan chiqarish (Ombor nazorati)
- **Inventarizatsiya**: ombor tanlang → «Qoldig‘i bor hamma pozitsiyani yuklash» → haqiqatda sanalgan miqdorni yozing → «O‘tkazish». Qoldiq sanalgan miqdorga tenglashadi; kamomad «Yo‘qotishlar» hisobotiga va foydaga ta’sir qiladi.
- **Hisobdan chiqarish**: pozitsiya, miqdor va sabab (brak, shikastlanish, yo‘qotish, muddati o‘tgan, boshqa) kiritiladi. Omborda yetarli qoldiq bo‘lishi shart.
- Hujjatni o‘chirsangiz qoldiq qaytadi; «Tiklash» bilan qayta kuchga kiradi. Hammasi o‘zgarishlar jurnalida qoladi.

## Brak
Ishlab chiqarish hujjatida har qatorda «Miqdor» (yaroqli) va «Brak». Brak omborga kirim bo‘lmaydi, lekin materiallar brak uchun ham sarflanadi (me’yor bo‘yicha). «Brak» hisobotida mahsulot kesimida brak foizi va summasi.

## Tannarx va haqiqiy foyda
- Material narxi = o‘rtacha xarid narxi. Mahsulot tannarxi = me’yor bo‘yicha materiallar + odatdagi brak ulushi + donabay ish haqi.
- «Tannarx» hisobotida har mahsulot uchun tannarx, o‘rtacha sotuv narxi va marja; «Mahsulot foydasi» hisobotida davr bo‘yicha tushum − tannarx. Umumiy «Foyda» hisobotida «Hisobdan chiqarish va kamomad» qatori ham bor.

## Ish haqi (donabay)
1. «Ish haqi → Ishchilar»: ishchilarni qo‘shing. «Narxlar»: har mahsulot uchun bir dona narxini yozing.
2. Ishlab chiqarish hujjatida «Brigada»ni belgilang: partiya haqi (yaroqli dona × narx) brigada a’zolariga teng bo‘linadi. Narx keyin o‘zgarsa, eski partiyalar haqi o‘zgarmaydi.
3. «Mukofot va ushlanmalar»: qo‘lda qo‘shimcha yoki ushlanma (− bilan).
4. Oylikni «Bank/Kassa»da «Ish haqi» moddasi va ishchini tanlab to‘laysiz. «Qaydnoma»da hisoblangan, to‘langan va to‘lanishi kerak summa ko‘rinadi.
5. Sanani tanlash: «Barcha davr», «Shu oy», «O‘tgan oy», «Shu yil» tugmalari yoki o‘zingiz Dan/Gacha kiritasiz (shu tugmalar «Hisobotlar»da ham bor).
6. Ishchi bilan akt sverka: qaydnomada ishchi qatoridagi «Akt sverka» tugmasi. Davr boshidagi qoldiq, har bir partiya, mukofot/ushlanma va to‘lov sanasi bilan, davr oxiridagi qoldiq. «Matn sifatida nusxalash» bilan Excel yoki xabarga ko‘chirasiz.

## Telegram, ovozli kiritish, telefon
- **Telegram**: «Xavfsizlik → Telegram» da kod oling, botga `/start KOD` yuboring. Pastda tugmalar chiqadi: 📋 Signallar, 📦 Ombor (pozitsiyani tanlang yoki nomini yozing), 💳 Qarzlar, 💵 Kassa, ⚙️ Sozlamalar (til, avto-xabarlar, ulanishni uzish) — faqat rolingizga ruxsat etilgani ko‘rinadi. Buyruqlar (/brief, /stock sement, /debts, /cash) ham ishlaydi. Muhim signallar o‘zi keladi. Bundan tashqari bot yangi buyurtma, jo‘natma, to‘lov va ishlab chiqarish haqida darrov xabar beradi, hujjat tahrirlansa, o‘chirilsa yoki tiklansa ham alohida xabar yuboradi (hujjat raqami va kim o‘zgartirgani bilan), kunlik xulosa yuboradi. ⚙️ Sozlamalar da: har bir xabar turini (buyurtma, jo‘natma, to‘lov, ishlab chiqarish, tahrirlar, o‘chirishlar, kunlik xulosa, signallar; yoki «Hammasini yoqish/o‘chirish») bosib yoqasiz/o‘chirasiz, xulosa vaqtini tanlaysiz (08:00 … 22:00) va 🌙 «Tunda ovozsiz» (22:00–07:00) ni yoqasiz: xabarlar keladi, lekin telefon jim turadi (faqat rolingizga tegishli turlar ko‘rinadi).
- **Ovoz**: AI yordamchi va «matndan hujjat» maydonlarida «Gapirish» tugmasi (Chrome/Edge/Safari). Til sahifa tiliga qarab tanlanadi; audio brauzer ishlab chiqaruvchisi xizmatida qayta ishlanishi mumkin.
- **Telefon**: jadvallar kartochkalarga aylanadi. **F5**: ochiq hujjat yorliqlari saqlanib qoladi (chiqishda o‘chadi).
- **Hisobotlar**: «Tugash prognozi» (necha kunga yetadi); AI signallarida takroriy hujjatlar belgilanadi.

## Xatolarni to‘g‘rilash
Hujjatni tahrirlash yoki o‘chirish mumkin (o‘chirilgani jurnalda qoladi va tiklanadi). Kim nimani o‘zgartirgani **O‘zgarishlar jurnali**da ko‘rinadi.


## Jonli yangilanish

Bir foydalanuvchi ma'lumotni saqlasa (hujjat, to'lov, mahsulot va hokazo), boshqalarning ochiq sahifalari 1-2 soniyada o'zi yangilanadi, sahifani qayta yuklash shart emas. Siz matn yozayotgan bo'lsangiz, yozishni tugatguningizcha sahifa qayta chizilmaydi. Aloqa uzilsa, o'zi qayta ulanadi va o'tkazib yuborgan o'zgarishlarni oladi.
Texnik: server `GET /api/events` orqali Server-Sent Events yuboradi (faqat "o'zgardi" xabari, ma'lumotsiz); API bitta jarayonda ishlaydi (bir nechta worker qo'yilsa, PostgreSQL LISTEN/NOTIFY kerak bo'ladi).

## Yuk xati (nakladnoy) chop etish
- Rasxodnoy nakladnoy saqlanganda «Yuk xatini chop etish» belgisi yoqilgan bo'lsa PDF o'zi ochiladi; ro'yxatdagi ⋮ menyusida va nakladnoy sahifasida ham «Yuk xati» tugmasi bor.
- Bitta gorizontal A4 varaqda ikki bir xil nusxa chiqadi: biri haydovchiga, biri bizda qoladi. Raqam — tizimdagi nakladnoy raqami (RN-…).
- Haydovchi va mashina raqamini nakladnoyda kiritasiz. Rekvizitlar (manzil, OKONX, hisob, MFO, INN, telefon) — Sozlamalar → Kompaniya.

## Telegram orqali ishlab chiqarishni kiritish
- Ishlab chiqarishni kiritish huquqi bor xodim (admin, ishlab chiqarish rahbari) botga oddiy matn yuboradi, har qatorda bitta mahsulot:
  ```
  14.10
  ФБС 24.4.6-Т - 40
  2ПК 66,5*10 25 dona
  Brigada: Ali, Vali
  ```
- Bir xil ro‘yxat (shu sana, shu mahsulotlar va sonlar) ikkinchi marta kiritilmaydi: bot avval kiritilgan PRD raqamini aytadi. Sana yoki son boshqacha bo‘lsa, kiritiladi.
- Mahsulotni qisqa yozsa ham bo‘ladi: `66*12-2`, `66:12-2` yoki `66x12-2` (2ПК 66*12 — 2 dona). Nom bir nechta mahsulotga mos kelsa, bot so‘raydi. Oxirida `Jami: 19 ta` yozilsa, bot yig‘indini tekshiradi; mos kelmasa hech narsa kiritilmaydi.
- Sana yozilmasa — bugun («bugun», «kecha» ham bo‘ladi). Brigada va «Ombor: …» qatorlari ixtiyoriy; ombor yozilmasa birinchi ishlab chiqarish ombori olinadi va ko‘rsatiladi.
- Bot o‘qib, nima tushunganini ko‘rsatadi. Oddiy xodim «✅ Rahbarga yuborish» bosadi: ro‘yxat adminga boradi va admin «✅ Tasdiqlayman» bosgandagina hisobga tushadi (xodimga natija xabari keladi). Admin rad etsa hech narsa kiritilmaydi. Admin o‘zi yuborsa, bitta «✅ Tasdiqlash» bilan darhol kiritiladi. «✖️ Bekor qilish» bilan yuboruvchi bekor qiladi. Ikki marta bosilsa ham bitta marta saqlanadi. Tasdiqlash muddati — 24 soat.
- Tasdiqlovchi — botga ulangan admin. Admin ulanmagan bo‘lsa, bot yuborib bo‘lmasligini aytadi.
- Biror qator tushunilmasa (mahsulot topilmasa, soni yo‘q, o‘lcham boshqa bo‘lsa) hech narsa kiritilmaydi, bot qaysi qator xato ekanini va o‘xshash nomlarni aytadi.
- Xomashyo yetmasa, bot buni oldindan aytadi va saqlashga yo‘l qo‘ymaydi (saytdagidek).
- Qo‘llanma: botda /prod.
