/* v2 layer: AI assistant / financier / analyst, reports center, audit journal, users, PDF printing.
   Loaded after the legacy pages. It adds its own views, routes and nav items and does not change the old screens. */
(function(){
'use strict';
var X={
 nav_ai:['AI assistant','AI-помощник','AI yordamchi'],nav_rep:['Reports','Отчёты','Hisobotlar'],nav_aud:['Change journal','Журнал изменений','O‘zgarishlar jurnali'],nav_usr:['Users','Пользователи','Foydalanuvchilar'],
 grp_ai:['Insight','Аналитика','Tahlil'],
 ai_h:['AI assistant','AI-помощник','AI yordamchi'],ai_note:['Ask about stock, orders, money and debts. The AI reads the same data your role can open and never changes anything.','Спрашивайте про остатки, заказы, деньги и долги. AI видит только то, что доступно вашей роли, и ничего не меняет.','Ombor, buyurtma, pul va qarzlar haqida so‘rang. AI faqat rolingiz ko‘ra oladigan ma’lumotni o‘qiydi va hech narsani o‘zgartirmaydi.'],
 m_assistant:['Assistant','Помощник','Yordamchi'],m_finance:['Financier','Финансист','Moliyachi'],m_analyst:['Analyst','Аналитик','Tahlilchi'],
 ai_ph:['Ask a question…','Задайте вопрос…','Savol yozing…'],ai_send:['Send','Отправить','Yuborish'],ai_think:['Looking at the data…','Смотрю данные…','Ma’lumotlarni ko‘ryapman…'],
 ai_off_h:['AI is not connected','AI не подключён','AI ulanmagan'],ai_off_p:['Add ANTHROPIC_API_KEY to the server .env file and restart. Until then the signals and reports below still work.','Добавьте ANTHROPIC_API_KEY в файл .env на сервере и перезапустите. Пока сигналы и отчёты ниже работают без AI.','Serverdagi .env fayliga ANTHROPIC_API_KEY ni qo‘shing va qayta ishga tushiring. Shu vaqtgacha pastdagi signallar va hisobotlar AI siz ishlaydi.'],
 ai_on:['AI connected','AI подключён','AI ulangan'],ai_clear:['New chat','Новый чат','Yangi suhbat'],
 ai_brief_daily:['Today’s briefing','Сводка на сегодня','Bugungi xulosa'],ai_brief_fin:['Financial briefing','Финансовая сводка','Moliyaviy xulosa'],ai_rule:['rule-based','по правилам','qoidalar asosida'],ai_ai:['AI','AI','AI'],ai_refresh:['Refresh','Обновить','Yangilash'],
 ai_signals:['Signals','Сигналы','Signallar'],ai_nosig:['Nothing needs attention right now.','Сейчас ничего не требует внимания.','Hozircha e’tibor talab qiladigan narsa yo‘q.'],
 ai_used:['Read:','Прочитано:','O‘qildi:'],
 s_a1:['How much cement is left?','Сколько осталось цемента?','Sement qancha qoldi?'],s_a2:['Who owes us money?','Кто нам должен?','Kim bizga qarz?'],s_a3:['Show the last 5 delivery notes','Покажи последние 5 накладных','Oxirgi 5 ta nakladnoyni ko‘rsat'],
 s_f1:['Cash flow for the last 30 days','Движение денег за 30 дней','So‘nggi 30 kunlik pul oqimi'],s_f2:['Whom should we collect from first?','С кого взыскать долг в первую очередь?','Birinchi kimdan qarz undirish kerak?'],s_f3:['Will the money last the next month?','Хватит ли денег на следующий месяц?','Keyingi oyga pul yetadimi?'],
 s_n1:['Which materials run out soonest?','Какие материалы закончатся раньше всего?','Qaysi materiallar tezroq tugaydi?'],s_n2:['How are sales trending?','Как идут продажи?','Sotuv qanday ketyapti?'],s_n3:['Which products sell slowly?','Какая продукция продаётся медленно?','Qaysi mahsulotlar sekin sotilyapti?'],
 tool_get_stock:['stock','остатки','ombor qoldig‘i'],tool_get_dashboard:['dashboard','дашборд','dashboard'],tool_get_insights:['signals','сигналы','signallar'],tool_run_report:['report','отчёт','hisobot'],tool_get_account_balances:['balances','остатки по счетам','hisob qoldiqlari'],tool_customer_statement:['customer act','акт покупателя','mijoz akti'],tool_supplier_statement:['supplier act','акт поставщика','yetkazib beruvchi akti'],tool_list_documents:['documents','документы','hujjatlar'],
 dr_h:['Fill a document with AI','Заполнить документ с AI','Hujjatni AI bilan to‘ldirish'],dr_note:['Paste a message or list, or attach a photo of an invoice. You review the draft in the normal form before anything is saved.','Вставьте сообщение или список либо приложите фото накладной. Вы проверите черновик в обычной форме, пока ничего не сохранено.','Xabar yoki ro‘yxatni joylang yoki nakladnoy rasmini biriktiring. Hech narsa saqlanmasdan oldin qoralamani oddiy shaklda tekshirasiz.'],
 dr_ph:['e.g. Cement Trade: 500 kg cement at 1 100, 20 rebar','напр. Cement Trade: 500 кг цемента по 1 100, 20 арматуры','masalan: Cement Trade dan 500 kg sement 1 100 dan, 20 armatura'],dr_photo:['Attach photo','Приложить фото','Rasm biriktirish'],dr_make:['Create draft','Создать черновик','Qoralama yaratish'],dr_open:['Open in form','Открыть в форме','Shaklda ochish'],dr_working:['Reading…','Читаю…','O‘qiyapman…'],
 dr_k_receipt:['Purchase receipt','Поступление','Kirim nakladnoy'],dr_k_invoice:['Delivery note','Накладная','Jo‘natma nakladnoy'],dr_k_order:['Customer order','Заказ покупателя','Mijoz buyurtmasi'],dr_k_payment_in:['Money received','Поступление денег','Pul kirimi'],dr_k_payment_out:['Money paid','Выплата','Pul chiqimi'],
 dr_k_production:['Production','Производство','Ishlab chiqarish'],dr_create:['Create document','Создать документ','Hujjatni yaratish'],dr_choose:['— choose —','— выберите —','— tanlang —'],dr_supplier:['Supplier','Поставщик','Yetkazib beruvchi'],dr_customer:['Customer','Покупатель','Mijoz'],dr_warehouse:['Warehouse','Склад','Ombor'],dr_plant:['Plant','Завод','Zavod'],dr_date:['Date','Дата','Sana'],dr_new_partner:['create new','создать нового','yangi qo‘shish'],dr_done:['Created: %s','Создан документ: %s','Yaratildi: %s'],
 dr_w_item_ambiguous:['Several similar items, choose one: %s','Несколько похожих позиций, выберите: %s','O‘xshash mahsulotlar bir nechta, tanlang: %s'],dr_w_item_wrong_kind:['This looks like the wrong kind of item: %s','Похоже, это позиция другого типа: %s','Boshqa turdagi mahsulotga o‘xshaydi: %s'],dr_w_unit_converted:['Unit converted: %s','Единицы пересчитаны: %s','Birlik qayta hisoblandi: %s'],dr_w_party_ambiguous:['Several similar partners, choose one: %s','Несколько похожих контрагентов, выберите: %s','O‘xshash hamkorlar bir nechta, tanlang: %s'],
 api_draft_incomplete:['The draft is incomplete: choose the partner, the warehouse and every item.','Черновик неполный: выберите контрагента, склад и все позиции.','Qoralama to‘liq emas: hamkor, ombor va barcha mahsulotlarni tanlang.'],
 dr_w_item_unmatched:['Item not found in the catalogue: %s','Позиция не найдена в справочнике: %s','Spravochnikda topilmadi: %s'],dr_w_party_unmatched:['Partner not found: %s','Контрагент не найден: %s','Hamkor topilmadi: %s'],dr_w_warehouse_unmatched:['Warehouse not found: %s','Склад не найден: %s','Ombor topilmadi: %s'],dr_w_bad_date:['Could not read the date: %s','Не удалось прочитать дату: %s','Sanani o‘qib bo‘lmadi: %s'],
 dr_need_partner:['Create this partner first, then open the draft again.','Сначала создайте этого контрагента и откройте черновик снова.','Avval shu hamkorni yarating, so‘ng qoralamani qayta oching.'],dr_item:['Written','Как написано','Yozilgan'],dr_match:['Matched','Найдено','Topilgan'],
 rp_h:['Reports','Отчёты','Hisobotlar'],rp_note:['Turnover, sales, purchases, money and debts for any period, with Excel export.','Оборотка, продажи, закупки, деньги и долги за любой период, с выгрузкой в Excel.','Oborotka, sotuv, xarid, pul va qarzlar istalgan davr uchun, Excelga yuklash bilan.'],
 dv_status_posted:['Posted','Проведён','O‘tkazilgan'],dv_status_draft:['Draft','Черновик','Qoralama'],dv_status_deleted:['Deleted','Удалён','O‘chirilgan'],dv_date:['Date','Дата','Sana'],dv_wh:['Warehouse','Склад','Ombor'],dv_party:['Counterparty','Контрагент','Kontragent'],dv_comment:['Comment','Комментарий','Izoh'],dv_item:['Item','Позиция','Pozitsiya'],dv_qty:['Quantity','Кол-во','Miqdor'],dv_price:['Price','Цена','Narx'],dv_sum:['Amount','Сумма','Summa'],dv_scrap:['Scrap','Брак','Brak'],dv_used:['Materials used','Израсходованные материалы','Sarflangan materiallar'],dv_sys:['In system','В системе','Tizimda'],dv_fact:['Counted','Факт','Haqiqiy'],dv_diff:['Difference','Разница','Farq'],dv_total:['Total','Итого','Jami'],dv_close:['Close','Закрыть','Yopish'],dv_view_only:['View only','Только просмотр','Faqat ko‘rish'],dv_open:['Click a row to view the document','Нажмите строку, чтобы открыть документ','Hujjatni ko‘rish uchun qatorni bosing'],rl_turnover:['Stock in, out and balance per item for a period','Приход, расход и остаток по каждой позиции за период','Davr uchun har bir pozitsiyaning kirimi, chiqimi va qoldig‘i'],rl_movements:['Every document line that moved stock, with a running balance','Каждая строка документа, изменившая остатки, с остатком после операции','Qoldiqni o‘zgartirgan har bir hujjat qatori va qoldiq'],rl_sales:['Sales by customer, item, day or month','Продажи по покупателям, позициям, дням и месяцам','Mijoz, pozitsiya, kun va oy bo‘yicha sotuv'],rl_purchases:['Purchases by supplier, item, day or month','Закупки по поставщикам, позициям, дням и месяцам','Yetkazib beruvchi, pozitsiya, kun va oy bo‘yicha xaridlar'],rl_cashflow:['Money in and out by article, day or account','Движение денег по статьям, дням и счетам','Moddalar, kunlar va hisoblar bo‘yicha pul kirimi va chiqimi'],rl_profit:['Estimated profit: sales minus material cost and expenses','Оценка прибыли: продажи минус материалы и расходы','Taxminiy foyda: sotuvdan xomashyo va xarajatlar ayriladi'],rl_plan:['What can be produced from the orders on hand','Что можно произвести по открытым заказам','Ochiq buyurtmalar bo‘yicha nima ishlab chiqarish kerak'],rl_plan_materials:['Which materials are short for the production plan','Каких материалов не хватает для плана производства','Ishlab chiqarish rejasi uchun qaysi xomashyo yetmaydi'],rl_debts_customer:['Who owes the plant and how much','Кто и сколько должен заводу','Mijozlar zavodga qancha qarzdor'],rl_aging:['Customer debts by how long they are overdue','Долги покупателей по срокам просрочки','Mijoz qarzlari muddati bo‘yicha'],rl_debts_supplier:['What the plant owes its suppliers','Сколько завод должен поставщикам','Zavodning yetkazib beruvchilarga qarzi'],rl_forecast:['How long each material will last at the current pace','На сколько хватит каждого материала при текущем темпе','Har bir xomashyo hozirgi sur’atda qancha vaqtga yetadi'],rl_losses:['Stock count differences and write-offs','Расхождения инвентаризации и списания','Inventarizatsiya farqlari va hisobdan chiqarishlar'],rl_production:['What was made: good and spoiled units by product, plant, day or month','Что произведено: годная продукция и брак по изделиям, заводам, дням и месяцам','Nima ishlab chiqarildi: mahsulot, zavod, kun yoki oy bo‘yicha yaroqli va brak soni'],rp_production:['Production','Производство','Ishlab chiqarish'],rp_note_production:['Only posted production documents. Good units went to stock; spoiled units are counted separately.','Только проведённые документы выпуска. Годные изделия ушли на склад, брак учтён отдельно.','Faqat o‘tkazilgan ishlab chiqarish hujjatlari. Yaroqlilari omborga tushgan, brak alohida hisoblanadi.'],g_warehouse:['Plant','Завод','Zavod'],g_warehouse_item:['Plant → product','Завод → изделие','Zavod → mahsulot'],g_day_item:['Day → product','День → изделие','Kun → mahsulot'],g_month_item:['Month → product','Месяц → изделие','Oy → mahsulot'],
rl_scrap:['Production scrap by product and period','Брак производства по продукции и периодам','Ishlab chiqarishdagi brak mahsulot va davr bo‘yicha'],rl_cost:['Cost price of each product from materials and labour','Себестоимость каждой продукции: материалы и труд','Har bir mahsulot tannarxi: xomashyo va mehnat'],rl_profit_products:['Profit per product sold','Прибыль по каждой проданной продукции','Sotilgan har bir mahsulot bo‘yicha foyda'],rl_payroll:['Piece-rate pay per worker for a period','Сдельная зарплата по рабочим за период','Davr uchun ishchilarning ishbay ish haqi'],rp_open_doc:['Open the document','Открыть документ','Hujjatni ochish'],rp_doc_na:['This document is not available for your role or has been deleted.','Документ недоступен для вашей роли или удалён.','Bu hujjat rolingiz uchun ochiq emas yoki o‘chirilgan.'],rp_movements:['Goods movement','Движение товаров','Tovarlar harakati'],rp_item:['Item','Позиция','Pozitsiya'],rp_doc:['Document type','Тип документа','Hujjat turi'],rp_d_production:['Production','Производство','Ishlab chiqarish'],rp_d_receipt:['Receipt','Поступление','Kirim nakladnoyi'],rp_d_invoice:['Delivery note','Расходная накладная','Chiqim nakladnoyi'],rp_d_adjust:['Count / write-off','Инвентаризация / списание','Inventarizatsiya / hisobdan chiqarish'],rp_note_movements:['Every document line that changed stock. Pick one item to see its opening balance and a running balance. Click a row in the stock turnover report to open that item here. Click a row here to view its document.','Каждая строка документа, изменившая остатки. Выберите позицию — увидите начальный остаток и остаток после каждой операции. Клик по строке в оборотной ведомости открывает позицию здесь. Клик по строке здесь открывает документ для просмотра.','Qoldiqni o‘zgartirgan har bir hujjat qatori. Bitta pozitsiyani tanlasangiz, boshlang‘ich qoldiq va har amaldan keyingi qoldiq ko‘rinadi. Oborot qaydnomasidagi qatorni bossangiz, pozitsiya shu yerda ochiladi. Bu yerdagi qatorni bossangiz, hujjat ko‘rish uchun ochiladi.'],rp_turnover:['Stock turnover','Оборотная ведомость','Oborot qaydnomasi'],rp_sales:['Sales','Продажи','Sotuv'],rp_purchases:['Purchases','Закупки','Xaridlar'],rp_cashflow:['Cash flow','Движение денег','Pul oqimi'],rp_profit:['Profit (estimate)','Прибыль (оценка)','Foyda (taxminiy)'],p_no_spec:['No specification: no materials will be consumed. You can add one later in Specifications.','Спецификации нет: материалы списываться не будут. Её можно добавить позже в разделе «Спецификации».','Spetsifikatsiya yo‘q: material sarflanmaydi. Uni keyinroq «Spetsifikatsiya» bo‘limida qo‘shishingiz mumkin.'],rp_plan:['Production plan','План производства','Ishlab chiqarish rejasi'],rp_plan_materials:['Material shortage','Нехватка материалов','Xomashyo yetishmasligi'],rp_debts_customer:['Customer debts','Долги покупателей','Mijozlar qarzi'],rp_debts_supplier:['Supplier debts','Долги поставщикам','Yetkazib beruvchilarga qarz'],
 rp_from:['From','С','Dan'],rp_to:['To','По','Gacha'],rp_group:['Group by','Группировать','Guruhlash'],rp_wh:['Warehouse','Склад','Ombor'],rp_all:['All','Все','Hammasi'],rp_kind:['Kind','Тип','Turi'],rp_xlsx:['Download Excel','Скачать Excel','Excel yuklab olish'],rp_total:['Total','Итого','Jami'],rp_empty:['No data for this period.','Нет данных за период.','Bu davr uchun ma’lumot yo‘q.'],rp_note_profit:['Estimate: shipped value minus materials at average purchase price minus operating expenses.','Оценка: стоимость отгрузок минус материалы по средней цене закупки минус операционные расходы.','Taxminiy: jo‘natilgan summa minus materiallar (o‘rtacha xarid narxida) minus xarajatlar.'],
 g_customer:['Customer','Покупатель','Mijoz'],g_supplier:['Supplier','Поставщик','Yetkazib beruvchi'],g_item:['Item','Позиция','Pozitsiya'],g_day:['Day','День','Kun'],g_month:['Month','Месяц','Oy'],g_article:['Article','Статья','Modda'],g_account:['Account','Счёт','Hisob'],k_product:['Products','Продукция','Mahsulot'],k_material:['Materials','Материалы','Material'],
 au_h:['Change journal','Журнал изменений','O‘zgarishlar jurnali'],au_note:['Who changed what and when. Written automatically; it cannot be edited.','Кто, что и когда изменил. Ведётся автоматически, изменить нельзя.','Kim, nimani va qachon o‘zgartirgan. Avtomatik yoziladi, tahrirlab bo‘lmaydi.'],
 au_time:['Time','Время','Vaqt'],au_user:['User','Пользователь','Foydalanuvchi'],au_action:['Action','Действие','Amal'],au_entity:['Record','Запись','Yozuv'],au_changes:['Changes','Изменения','O‘zgarishlar'],au_more:['Show more','Показать ещё','Yana ko‘rsatish'],
 a_create:['created','создал','yaratdi'],a_update:['changed','изменил','o‘zgartirdi'],a_delete:['deleted','удалил','o‘chirdi'],a_restore:['restored','восстановил','tikladi'],a_login:['signed in','вошёл','kirdi'],au_rows:['rows changed','строки изменены','qatorlar o‘zgargan'],au_pw:['password','пароль','parol'],
 e_orders:['Order','Заказ','Buyurtma'],e_invoices:['Delivery note','Накладная','Nakladnoy'],e_receipts:['Receipt','Поступление','Kirim'],e_production_docs:['Production','Производство','Ishlab chiqarish'],e_fin_docs:['Money document','Денежный документ','Pul hujjati'],e_customers:['Customer','Покупатель','Mijoz'],e_suppliers:['Supplier','Поставщик','Yetkazib beruvchi'],e_items:['Item','Позиция','Pozitsiya'],e_accounts:['Account','Счёт','Hisob'],e_warehouses:['Warehouse','Склад','Ombor'],e_units:['Unit','Единица','Birlik'],e_users:['User','Пользователь','Foydalanuvchi'],e_norms:['Specification','Спецификация','Spetsifikatsiya'],

 nav_sec:['Security','Безопасность','Xavfsizlik'],
 api_weak_password:['Use at least 10 characters, with letters and a digit.','Пароль: не короче 10 символов, буквы и цифра.','Parol: kamida 10 belgi, harf va raqam bilan.'],
 api_weak_too_short:['Use at least 10 characters.','Пароль — не короче 10 символов.','Parol kamida 10 belgidan iborat bo‘lsin.'],
 api_weak_need_letter_and_digit:['Use letters and at least one digit.','Нужны буквы и хотя бы одна цифра.','Harflar va kamida bitta raqam kerak.'],
 api_weak_too_common:['This password is too easy to guess. Avoid common words and your username.','Слишком простой пароль. Не используйте частые слова и свой логин.','Parol juda oson. Keng tarqalgan so‘zlar va loginingizdan foydalanmang.'],
 api_otp_required:['Enter the 6-digit code from your authenticator app.','Введите 6-значный код из приложения-аутентификатора.','Autentifikator ilovasidagi 6 xonali kodni kiriting.'],
 api_bad_otp:['The code is wrong or already used.','Код неверный или уже использован.','Kod noto‘g‘ri yoki allaqachon ishlatilgan.'],
 api_2fa_required:['Set up two-factor sign-in first.','Сначала включите двухфакторный вход.','Avval ikki bosqichli kirishni yoqing.'],
 api_2fa_on:['Two-factor sign-in is already on.','Двухфакторный вход уже включён.','Ikki bosqichli kirish allaqachon yoqilgan.'],
 api_2fa_state:['Start the setup first.','Сначала начните настройку.','Avval sozlashni boshlang.'],
 api_2fa_mandatory:['Your role must keep two-factor sign-in on.','Для вашей роли двухфакторный вход обязателен.','Roliingiz uchun ikki bosqichli kirish majburiy.'],
 sc_h:['Security','Безопасность','Xavfsizlik'],sc_note:['Your password, two-factor sign-in and the browsers signed in to your account.','Ваш пароль, двухфакторный вход и браузеры, выполнившие вход в ваш аккаунт.','Parolingiz, ikki bosqichli kirish va hisobingizga kirgan brauzerlar.'],
 sc_must:['Your role must set up two-factor sign-in before using the system. Do it below.','Для вашей роли нужно включить двухфакторный вход, иначе система недоступна. Сделайте это ниже.','Roliingiz tizimdan foydalanishdan oldin ikki bosqichli kirishni yoqishi shart. Quyida bajaring.'],
 sc_pw:['Password','Пароль','Parol'],sc_pw_note:['At least 10 characters with letters and a digit. Changing it signs out your other browsers.','От 10 символов, буквы и цифра. После смены остальные браузеры выйдут из аккаунта.','Kamida 10 belgi, harf va raqam. Almashtirgach boshqa brauzerlardan chiqib ketiladi.'],
 sc_2fa:['Two-factor sign-in','Двухфакторный вход','Ikki bosqichli kirish'],
 sc_2fa_off:['Off. A stolen password alone is enough to sign in.','Выключен. Для входа достаточно украденного пароля.','O‘chiq. Kirish uchun o‘g‘irlangan parolning o‘zi yetadi.'],
 sc_2fa_on:['On. Sign-in needs your password and a code from your phone.','Включён. Для входа нужны пароль и код из телефона.','Yoqilgan. Kirish uchun parol va telefondagi kod kerak.'],
 sc_2fa_start:['Turn on','Включить','Yoqish'],
 sc_2fa_scan:['1. Open Google Authenticator or Microsoft Authenticator and scan this code. 2. Enter the 6 digits it shows.','1. Откройте Google Authenticator или Microsoft Authenticator и отсканируйте код. 2. Введите 6 цифр из приложения.','1. Google Authenticator yoki Microsoft Authenticator ni oching va kodni skanerlang. 2. Ilovadagi 6 ta raqamni kiriting.'],
 sc_2fa_key:['Cannot scan? Enter this key by hand:','Не удаётся отсканировать? Введите ключ вручную:','Skanerlab bo‘lmasa, kalitni qo‘lda kiriting:'],
 sc_code:['6-digit code','6-значный код','6 xonali kod'],sc_confirm:['Confirm','Подтвердить','Tasdiqlash'],sc_cancel:['Cancel','Отмена','Bekor qilish'],
 sc_2fa_done:['Two-factor sign-in is on','Двухфакторный вход включён','Ikki bosqichli kirish yoqildi'],sc_2fa_gone:['Two-factor sign-in is off','Двухфакторный вход выключен','Ikki bosqichli kirish o‘chirildi'],
 sc_off_btn:['Turn off','Выключить','O‘chirish'],sc_off_pw:['Your password','Ваш пароль','Parolingiz'],
 sc_sess:['Signed-in browsers','Браузеры с входом','Kirilgan brauzerlar'],sc_sess_note:['If you do not recognise one, sign it out and change your password.','Если не узнаёте один из них, завершите его сеанс и смените пароль.','Notanish bo‘lsa, uni chiqarib yuboring va parolni almashtiring.'],
 sc_this:['This browser','Этот браузер','Shu brauzer'],sc_out:['Sign out','Выйти','Chiqarish'],sc_out_all:['Sign out all others','Выйти на всех остальных','Boshqalarini chiqarish'],sc_out_ok:['Signed out','Сеанс завершён','Chiqarildi'],
 sc_seen:['last active','активность','oxirgi faollik'],sc_since:['signed in','вход','kirgan'],
 us_prem:['Monthly meeting (premium)','Совещание (премиум)','Oylik majlis (premium)'],
 us_p_on:['Switch on for a month','Включить на месяц','Bir oyga yoqish'],us_p_on_s:['Switch on','Включить','Yoqish'],us_p_renew:['Renew','Продлить','Yangilash'],us_p_off:['Switch off','Выключить','O‘chirish'],
 us_p_until:['until','до','gacha'],us_p_left:['meetings left','совещаний осталось','ta majlis qoldi'],us_p_end:['expired','срок истёк','muddati tugagan'],us_p_always:['always on','всегда доступно','doim ochiq'],us_p_done:['Premium updated','Премиум обновлён','Premium yangilandi'],
 us_reset2fa:['Reset 2FA','Сбросить 2FA','2FA ni tiklash'],us_2fa_reset:['Two-factor sign-in reset','Двухфакторный вход сброшен','Ikki bosqichli kirish tiklandi'],
 us_h:['Users','Пользователи','Foydalanuvchilar'],us_note:['Accounts, roles and passwords. Only administrators can change them.','Учётные записи, роли и пароли. Менять могут только администраторы.','Hisoblar, rollar va parollar. Faqat administratorlar o‘zgartira oladi.'],
 us_name:['Full name','Имя','F.I.Sh.'],us_login:['Username','Логин','Login'],us_role:['Role','Роль','Rol'],us_pw:['Password (10+ characters)','Пароль (от 10 символов)','Parol (kamida 10 belgi)'],us_add:['Add user','Добавить','Qo‘shish'],us_active:['Active','Активен','Faol'],us_reset:['New password','Новый пароль','Yangi parol'],us_save:['Save','Сохранить','Saqlash'],us_saved:['Saved','Сохранено','Saqlandi'],us_off:['Disabled','Отключён','O‘chirilgan'],
 pw_h:['Change my password','Сменить мой пароль','Parolimni almashtirish'],pw_old:['Current password','Текущий пароль','Joriy parol'],pw_new:['New password (10+ characters)','Новый пароль (от 10 символов)','Yangi parol (kamida 10 belgi)'],pw_ok:['Password changed','Пароль изменён','Parol almashtirildi'],pw_btn:['Change password','Сменить пароль','Parolni almashtirish'],close:['Close','Закрыть','Yopish'],
 pdf_print:['Print PDF','Печать PDF','PDF chop etish'],pdf_dl:['Download','Скачать','Yuklab olish'],pdf_prt:['Print','Печать','Chop etish'],pdf_close:['Close','Закрыть','Yopish'],pdf_hint:['If the page below is empty, press Download.','Если ниже пусто, нажмите «Скачать».','Pastda bo‘sh bo‘lsa, «Yuklab olish» ni bosing.'],ai_box_h:['AI briefing','AI-сводка','AI xulosa'],ai_box_more:['Open assistant','Открыть помощника','Yordamchini ochish'],sev_crit:['Urgent','Срочно','Shoshilinch'],sev_warn:['Watch','Внимание','Diqqat'],sev_info:['Info','Информация','Ma’lumot'],
 api_ai_disabled:['AI is not configured: set ANTHROPIC_API_KEY or GEMINI_API_KEY on the server.','AI не настроен: задайте ANTHROPIC_API_KEY или GEMINI_API_KEY на сервере.','AI sozlanmagan: serverda ANTHROPIC_API_KEY yoki GEMINI_API_KEY ni kiriting.'],api_ai_bad_key:['The AI key was rejected. Check ANTHROPIC_API_KEY.','Ключ AI отклонён. Проверьте ANTHROPIC_API_KEY.','AI kaliti qabul qilinmadi. ANTHROPIC_API_KEY ni tekshiring.'],api_ai_bad_model:['The AI model is not available. Change GEMINI_MODEL in .env.','Модель AI недоступна. Измените GEMINI_MODEL в .env.','AI modeli mavjud emas. .env da GEMINI_MODEL ni almashtiring.'],api_ai_busy:['The AI service is busy. Try again shortly.','Сервис AI занят. Повторите чуть позже.','AI xizmati band. Birozdan so‘ng qayta urinib ko‘ring.'],api_ai_unreachable:['The AI service cannot be reached from the server.','Сервер не может связаться с сервисом AI.','Server AI xizmatiga ulana olmadi.'],api_ai_error:['The AI service returned an error.','Сервис AI вернул ошибку.','AI xizmati xatolik qaytardi.'],api_empty_message:['Write something first.','Сначала напишите текст.','Avval biror narsa yozing.'],api_bad_image:['Use a JPEG, PNG or WebP image under 5 MB.','Нужно изображение JPEG, PNG или WebP до 5 МБ.','5 MB gacha JPEG, PNG yoki WebP rasm kerak.'],api_draft_failed:['No document could be read from this input.','Из этих данных не удалось получить документ.','Bu ma’lumotdan hujjat o‘qib bo‘lmadi.'],
 api_premium_required:['This is a premium feature. Ask the administrator to switch it on.','Это премиум-функция. Попросите администратора включить её.','Bu premium imkoniyat. Yoqish uchun administratorga murojaat qiling.'],api_owner_only:['Only the main administrator can switch premium features on.','Премиум-функции включает только главный администратор.','Premium imkoniyatlarni faqat asosiy administrator yoqa oladi.'],
 api_too_many_attempts:['Too many attempts. Wait a few minutes and try again.','Слишком много попыток. Подождите несколько минут.','Urinishlar juda ko‘p. Bir necha daqiqa kuting.'],api_last_admin:['At least one active administrator must remain.','Должен остаться хотя бы один активный администратор.','Kamida bitta faol administrator qolishi kerak.'],api_self_disable:['You cannot disable your own account.','Нельзя отключить собственную запись.','O‘z hisobingizni o‘chira olmaysiz.'],api_weak_password:['Use at least 8 characters.','Пароль — не короче 8 символов.','Parol kamida 8 belgidan iborat bo‘lsin.'],api_bad_password:['The current password is wrong.','Текущий пароль неверный.','Joriy parol noto‘g‘ri.'],api_bad_role:['Unknown role.','Неизвестная роль.','Noma’lum rol.']
};
Object.assign(X,{
 cu_terms:['Payment term, days','Срок оплаты, дней','To‘lov muddati, kun'],
 cu_terms_h:['Delivery notes get a pay-by date this many days after delivery. 0 = due on delivery.','Накладным ставится срок оплаты через столько дней после отгрузки. 0 = в день отгрузки.','Nakladnoyga yetkazishdan shuncha kun keyingi to‘lov sanasi qo‘yiladi. 0 = yetkazilgan kuni.'],
 cu_overdue:['Overdue','Просрочено','Muddati o‘tgan'],
 iv_pay:['Pay by','Оплатить до','To‘lov muddati'],iv_pay_hint:['Empty = by the customer’s term','Пусто = по сроку покупателя','Bo‘sh = mijoz muddati bo‘yicha'],
 f_order:['Advance for order','Аванс по заказу','Buyurtma uchun avans'],f_order_none:['— not an advance —','— не аванс —','— avans emas —'],
 c_adv:['Advance','Аванс','Avans'],
 bz_overdue:['Overdue payments','Просроченные оплаты','Muddati o‘tgan to‘lovlar'],bz_sub_overdue:['%n customers','%n покупателей','%n ta mijoz'],
 rp_aging:['Debt age','Возраст долгов','Qarz yoshi'],rp_note_aging:['Unpaid delivery notes by days past the pay-by date. Payments are applied to the oldest notes first; money paid ahead is shown as an advance.','Неоплаченные накладные по дням просрочки. Оплаты зачитываются в самые старые накладные; переплата показана как аванс.','To‘lanmagan nakladnoylar muddatdan o‘tgan kunlar bo‘yicha. To‘lovlar eng eski nakladnoylarga yopiladi; oldindan to‘langan summa avans sifatida ko‘rsatiladi.'],
 api_order_mismatch:['The order does not belong to this customer.','Заказ не принадлежит этому покупателю.','Buyurtma bu mijozga tegishli emas.']
});
Object.assign(X,{
 tg_h:['Telegram','Telegram','Telegram'],tg_on:['This account is linked to Telegram. In the bot: /brief, /stock, /debts, /cash. Send /alerts off to stop automatic alerts.','Аккаунт привязан к Telegram. В боте: /brief, /stock, /debts, /cash. /alerts off — отключить авто-уведомления.','Hisob Telegram’ga ulangan. Botda: /brief, /stock, /debts, /cash. Avto-xabarlarni to‘xtatish: /alerts off.'],tg_off:['Get signals and quick answers in Telegram, limited to what your role may see.','Получайте сигналы и быстрые ответы в Telegram — только то, что разрешено вашей роли.','Signal va tezkor javoblarni Telegram’da oling — faqat rolingizga ruxsat etilgani.'],tg_code:['Get a link code','Получить код привязки','Ulash kodini olish'],tg_unlink:['Disconnect Telegram','Отвязать Telegram','Telegram’ni uzish'],tg_steps:['Open the bot in Telegram and send this message:','Откройте бота в Telegram и отправьте сообщение:','Telegram’da botni oching va quyidagini yuboring:'],tg_valid:['valid for 10 minutes, one use','действует 10 минут, один раз','10 daqiqa amal qiladi, bir marta'],tg_gone:['Telegram disconnected.','Telegram отвязан.','Telegram uzildi.'],api_telegram_off:['The Telegram bot is not set up on the server.','Telegram-бот не настроен на сервере.','Telegram bot serverda sozlanmagan.'],
 rp_forecast:['Stock-out forecast','Прогноз остатков','Tugash prognozi'],rp_note_forecast:['Days of cover at the average use of the last 30 days (materials used in production, goods shipped). Shortest first.','На сколько дней хватит остатка при среднем расходе за 30 дней (материалы в производство, отгрузки). Сначала самые короткие.','So‘nggi 30 kunlik o‘rtacha sarfda qoldiq necha kunga yetishi (ishlab chiqarishga materiallar, jo‘natmalar). Eng qisqalari birinchi.'],
 rp_losses:['Losses','Потери','Yo‘qotishlar'],rp_scrap:['Scrap','Брак','Brak'],rp_cost:['Product cost','Себестоимость','Tannarx'],rp_profit_products:['Profit by product','Прибыль по продукции','Mahsulot foydasi'],rp_payroll:['Pay statement','Ведомость','Ish haqi qaydnomasi'],
 rp_note_losses:['Write-offs and count shortages valued at the average cost. Surpluses reduce the loss.','Списания и недостачи по инвентаризации по средней себестоимости. Излишки уменьшают потери.','Hisobdan chiqarish va inventarizatsiya kamomadi o‘rtacha tannarxda. Ortiqcha miqdor yo‘qotishni kamaytiradi.'],
 rp_note_scrap:['Spoiled units against good units. The materials of spoiled units are already in the material cost.','Брак к годной продукции. Материалы брака уже входят в материальные затраты.','Brak yaroqli mahsulotga nisbatan. Brak materiallari allaqachon material xarajatida.'],
 rp_note_cost:['Materials by the norms at the average purchase price, plus the usual scrap and piece pay. Price is the average shipped price.','Материалы по нормам по средней закупочной цене, плюс обычный брак и сдельная оплата. Цена — средняя цена отгрузки.','Materiallar me’yor bo‘yicha o‘rtacha xarid narxida, odatdagi brak va donabay ish haqi bilan. Narx — o‘rtacha jo‘natish narxi.'],
 rp_note_pprod:['Shipped value minus the cost of the products shipped.','Выручка минус себестоимость отгруженной продукции.','Jo‘natilgan summa minus jo‘natilgan mahsulot tannarxi.'],
 rp_note_payroll:['Earned by crew shares of piece pay, plus bonuses and deductions, minus salary paid to the worker.','Начислено по долям бригады, плюс премии и удержания, минус выплаченная зарплата.','Brigada ulushlari bo‘yicha hisoblangan donabay haq, mukofot va ushlanmalar bilan, to‘langan oylik ayirilgan.'],
 nav_adj:['Counts & write-offs','Инвентаризация','Inventarizatsiya'],nav_pay:['Pay & workers','Зарплата','Ish haqi']
});
Object.keys(X).forEach(function(k){T.en[k]=X[k][0];T.ru[k]=X[k][1];T.uz[k]=X[k][2]});

/* ---- nav, icons, levels, routes ---- */
NI.ai='<path d="M10 2.5l1.6 4.4 4.4 1.6-4.4 1.6L10 14.5l-1.6-4.4L4 8.5l4.4-1.6zM15.5 12.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>';
NI.rep='<path d="M4 17V9M9 17V4M14 17v-6M2.5 17.5h15"/>';
NI.aud='<path d="M10 3.5v6.5l3.5 2M17 10a7 7 0 11-2.1-5"/><path d="M17 3v3.5h-3.5"/>';
NI.usr='<circle cx="10" cy="7" r="3"/><path d="M4 17c.7-3.2 3-4.8 6-4.8s5.3 1.6 6 4.8"/>';
NI.key='<circle cx="6.5" cy="13.5" r="3"/><path d="M8.8 11.2L16 4M13 7l2.5 2.5"/>';
NAV.splice(NAV.length-1,0,{g:'grp_ai',i:[['ai','assistant','nav_ai'],['rep','reports','nav_rep']]});
NAV[NAV.length-1].i.push(['aud','journal','nav_aud'],['usr','users','nav_usr'],['sec','security','nav_sec']);NI.sec='<path d="M10 2.5l6 2.2v4.6c0 3.8-2.5 6.7-6 8.2-3.5-1.5-6-4.4-6-8.2V4.7z"/><path d="M7.5 10l1.8 1.8L13 8"/>';
NAV.forEach(function(g){g.i.forEach(function(x){SECHASH[x[0]]=x[1]})});
var _uf=userFrom;
userFrom=function(m){var u=_uf(m),l=u.levels||{};u.levels=l;
  l.ai=2;l.rep=(l.wh||l.inv||l.rec||l.bank||l.cash||l.cus||l.sup)?2:0;l.aud=(u.owner&&l.set>=1)?2:0;l.usr=l.set>=1?l.set:0;l.sec=2;return u};
var _so=secOf;
var VIEWS=['assistant','reports','journal','users','security'],VSEC={assistant:'ai',reports:'rep',journal:'aud',users:'usr',security:'sec'};
var RENDER={assistant:function(){renderAi()},reports:function(){renderRep()},journal:function(){renderAud()},users:function(){renderUsr()},security:function(){renderSec()}};
secOf=function(h){return VSEC[h]||_so(h)};
var main=document.querySelector('main');
function mkView(v){var d=document.createElement('div');d.id='xv-'+v;d.hidden=true;main.appendChild(d)}
VIEWS.forEach(mkView);
/* later scripts add their own pages: addView(hash, section, render) */
window.addView=function(name,sec,fn){VIEWS.push(name);VSEC[name]=sec;RENDER[name]=fn;mkView(name)};
var _rc=routeCore;
routeCore=function(){
  var h=(location.hash||'').replace('#','');
  if(VIEWS.indexOf(h)<0){VIEWS.forEach(function(v){$('#xv-'+v).hidden=true});_rc();if(h==='dashboard')renderAiBox();return}
  ['home','dash','login','prod','wh','items','specs','mats','cus','ord','inv','pur','set','fin'].forEach(function(v){var e=$('#view-'+v);if(e)e.hidden=true});
  VIEWS.forEach(function(v){$('#xv-'+v).hidden=(v!==h)});
  document.querySelectorAll('.nav a,.side a').forEach(function(l){l.removeAttribute('aria-current')});
  var n=$('#nav-'+VSEC[h]);if(n)n.setAttribute('aria-current','page');
  closeMenu();prevH=h;window.scrollTo(0,0);
  RENDER[h]();
};

/* ---- helpers ---- */
function J(o){return JSON.stringify(o)}
function Q(o){var a=[];Object.keys(o).forEach(function(k){if(o[k]!==''&&o[k]!=null)a.push(encodeURIComponent(k)+'='+encodeURIComponent(o[k]))});return a.length?'?'+a.join('&'):''}
function errText(e){return apiErr(e)}
function num(v,type){
  if(v==null||v==='')return '';
  if(type==='money')return money(v);
  if(type==='num')return (Math.round(v*1000)/1000).toLocaleString(LOC[lang],{maximumFractionDigits:3});
  if(type==='int')return String(v);
  return esc(v);
}
function tableHtml(tb){
  if(!tb.rows.length)return '<p class="empty">'+t('rp_empty')+'</p>';
  var th='<thead><tr>'+tb.columns.map(function(c){return '<th'+(/money|num|int/.test(c.type)?' class="num"':'')+'>'+esc(tb.labels[c.key]||c.key)+'</th>'}).join('')+'</tr></thead>';
  var tr=tb.rows.map(function(r){return '<tr>'+tb.columns.map(function(c){var v=r[c.key];var cls=/money|num|int/.test(c.type)?' class="num"'+(c.type==='money'&&v<0?' style="color:var(--bad)"':''):'';return '<td'+cls+'>'+num(v,c.type)+'</td>'}).join('')+'</tr>'}).join('');
  var tf='';
  if(tb.totals&&Object.keys(tb.totals).length)tf='<tfoot><tr>'+tb.columns.map(function(c,i){return '<td'+(/money|num|int/.test(c.type)?' class="num"':'')+'>'+(i===0&&!(c.key in tb.totals)?t('rp_total'):(c.key in tb.totals?num(tb.totals[c.key],c.type):''))+'</td>'}).join('')+'</tr></tfoot>';
  return '<div style="overflow-x:auto"><table class="dt">'+th+'<tbody>'+tr+'</tbody>'+tf+'</table></div>';
}
function openBlob(path,name,download){
  /* downloads go straight to a file; PDFs open in an in-page viewer (no pop-up window, so pop-up blockers cannot get in the way) */
  fetch(API.base+path,{headers:{Authorization:'Bearer '+API.token}}).then(function(r){
    if(!r.ok)return r.json().catch(function(){return {}}).then(function(j){var d=(j&&j.detail)||{};var e=new Error(d.message||'error');e.code=d.code||'error';e.params=d.params||{};throw e});
    return r.blob();
  }).then(function(b){
    if(!download&&/\.pdf$/i.test(name||''))return pdfView(new Blob([b],{type:'application/pdf'}),name);
    saveBlob(b,name);
  }).catch(function(e){toast(errText(e),true)});
}
window.openBlob=openBlob;
function saveBlob(b,name){
  var u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=name||'file';document.body.appendChild(a);a.click();a.remove();
  setTimeout(function(){URL.revokeObjectURL(u)},15000);
}
function pdfView(blob,name){
  var old=document.getElementById('pdfv');if(old)old.remove();
  var u=URL.createObjectURL(blob),box=document.createElement('div');box.id='pdfv';box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label',name||'PDF');
  box.innerHTML='<div class="pdfbar"><b>'+esc(name||'PDF')+'</b><span class="note">'+t('pdf_hint')+'</span><span class="sp"></span>'+
    '<button type="button" class="btn primary sm" data-a="dl">'+t('pdf_dl')+'</button><button type="button" class="btn ghost sm" data-a="pr">'+t('pdf_prt')+'</button><button type="button" class="btn ghost sm" data-a="x">'+t('pdf_close')+'</button></div>'+
    '<iframe title="'+esc(name||'PDF')+'" src="'+u+'"></iframe>';
  function close(){document.removeEventListener('keydown',key);box.remove();document.body.classList.remove('pdf-open');setTimeout(function(){URL.revokeObjectURL(u)},1000)}
  function key(e){if(e.key==='Escape')close()}
  box.addEventListener('click',function(e){var b=e.target.closest('[data-a]');if(!b)return;var a=b.dataset.a;
    if(a==='x')close();else if(a==='dl')saveBlob(blob,name);
    else if(a==='pr'){try{var f=box.querySelector('iframe');f.contentWindow.focus();f.contentWindow.print()}catch(x){saveBlob(blob,name)}}});
  document.addEventListener('keydown',key);document.body.classList.add('pdf-open');document.body.appendChild(box);
  box.querySelector('[data-a=x]').focus();
}
function md(s){
  var lines=esc(String(s)).split('\n'),out=[],list=null,tbl=null;
  function close(){if(list){out.push('</'+list+'>');list=null}if(tbl){out.push(tbl+'</tbody></table></div>');tbl=null}}
  function inl(x){return x.replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`(.+?)`/g,'<code>$1</code>')}
  lines.forEach(function(l){
    var m;
    if(/^\s*\|.*\|\s*$/.test(l)){
      if(/^\s*\|[\s:|-]+\|\s*$/.test(l))return;
      var cells=l.trim().replace(/^\||\|$/g,'').split('|').map(function(c){return inl(c.trim())});
      if(!tbl){close();tbl='<div style="overflow-x:auto"><table class="dt"><thead><tr>'+cells.map(function(c){return '<th>'+c+'</th>'}).join('')+'</tr></thead><tbody>';return}
      tbl+='<tr>'+cells.map(function(c){return '<td>'+c+'</td>'}).join('')+'</tr>';return;
    }
    if((m=l.match(/^\s*[-*•]\s+(.*)/))){if(list!=='ul'){close();out.push('<ul>');list='ul'}out.push('<li>'+inl(m[1])+'</li>');return}
    if((m=l.match(/^\s*\d+[.)]\s+(.*)/))){if(list!=='ol'){close();out.push('<ol>');list='ol'}out.push('<li>'+inl(m[1])+'</li>');return}
    close();
    if((m=l.match(/^#{1,4}\s+(.*)/))){out.push('<h4>'+inl(m[1])+'</h4>');return}
    out.push(l.trim()?'<p>'+inl(l)+'</p>':'');
  });
  close();return out.join('');
}
function fillSel(el,opts,val){el.innerHTML=opts.map(function(o){return '<option value="'+esc(o[0])+'">'+esc(o[1])+'</option>'}).join('');if(val!=null)el.value=val}

/* ---- AI page ---- */
var AI={mode:'assistant',msgs:{assistant:[],finance:[],analyst:[]},busy:false,on:null,brief:{},sig:null,draft:null,img:null,dbusy:false};
var SUG={assistant:['s_a1','s_a2','s_a3'],finance:['s_f1','s_f2','s_f3'],analyst:['s_n1','s_n2','s_n3']};
function aiStatus(){return api('GET','/ai/status').then(function(s){AI.on=!!s.enabled},function(){AI.on=false})}
function renderAi(){
  var el=$('#xv-assistant');
  if(!el.firstChild){
    el.innerHTML='<div class="wrap dash"><div class="dhead"><div><h1 id="ai-h"></h1><p class="note" id="ai-note"></p></div><span class="pill" id="ai-state"></span></div>'+
     '<div class="seg" id="ai-modes" role="group" style="justify-self:start"></div>'+
     '<div class="aigrid"><div class="stack">'+
       '<div class="panel aichat"><div class="aioff" id="ai-off" hidden></div><div class="ailog" id="ai-log" aria-live="polite"></div>'+
       '<div class="aisug" id="ai-sug"></div>'+
       '<form class="aiform" id="ai-form"><textarea id="ai-in" rows="2" maxlength="2000"></textarea><div class="aibtns"><button type="submit" class="btn primary sm" id="ai-send"></button><button type="button" class="btn ghost sm" id="ai-clear"></button></div></form></div>'+
       '<div class="panel stack" id="ai-draft"></div>'+
     '</div><div class="stack"><div class="panel" id="ai-brief"></div><div class="panel" id="ai-sig"></div></div></div></div>';
    $('#ai-form').addEventListener('submit',function(e){e.preventDefault();aiSend($('#ai-in').value)});
    $('#ai-in').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();aiSend(this.value)}});
    $('#ai-clear').addEventListener('click',function(){AI.msgs[AI.mode]=[];aiLog();});
    $('#ai-sug').addEventListener('click',function(e){var b=e.target.closest('button');if(b)aiSend(b.textContent)});
    $('#ai-modes').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;AI.mode=b.dataset.m;aiChrome();aiLog();aiBrief(true)});
    el.addEventListener('click',function(e){
      if(e.target.closest('#ai-brief-r'))aiBrief(true,true);
      if(e.target.closest('#dr-make'))aiDraft();
      if(e.target.closest('#dr-open'))openDraft(AI.draft);
      if(e.target.closest('#dr-create'))draftCreate();
      if(e.target.closest('#dr-clear')){AI.img=null;$('#dr-file').value='';$('#dr-img').textContent=''}
    });
    el.addEventListener('change',function(e){if(e.target.id==='dr-file')pickImage(e.target.files[0]);else draftChange(e)});
  }
  aiChrome();aiLog();aiDraftUi();
  aiStatus().then(function(){aiChrome()});
  aiBrief(false);aiSignals();
}
function aiChrome(){
  $('#ai-h').textContent=t('ai_h');$('#ai-note').textContent=t('ai_note');
  var on=AI.on;$('#ai-state').innerHTML=on===null?'':'<svg width="10" height="10" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="'+(on?'var(--good)':'var(--warn)')+'"/></svg>'+(on?t('ai_on'):t('ai_off_h'));
  var off=$('#ai-off');off.hidden=on!==false;off.innerHTML='<b>'+t('ai_off_h')+'</b><span>'+t('ai_off_p')+'</span>';
  $('#ai-modes').innerHTML=['assistant','finance','analyst'].filter(function(m){return m==='assistant'||(m==='finance'&&(lvl('bank')||lvl('cash')||lvl('cus')||lvl('sup')||lvl('inv')))||(m==='analyst'&&(lvl('wh')||lvl('inv')))}).map(function(m){return '<button type="button" data-m="'+m+'" aria-pressed="'+(AI.mode===m)+'">'+t('m_'+m)+'</button>'}).join('');
  $('#ai-in').placeholder=t('ai_ph');$('#ai-send').textContent=t('ai_send');$('#ai-clear').textContent=t('ai_clear');
  $('#ai-sug').innerHTML=SUG[AI.mode].map(function(k){return '<button type="button" class="tag">'+esc(t(k))+'</button>'}).join('');
}
function aiLog(){
  var log=$('#ai-log'),ms=AI.msgs[AI.mode];
  log.innerHTML=ms.map(function(m){
    if(m.role==='user')return '<div class="aib me">'+esc(m.content).replace(/\n/g,'<br>')+'</div>';
    return '<div class="aib bot'+(m.err?' err':'')+'">'+(m.err?esc(m.content):md(m.content))+(m.tools&&m.tools.length?'<div class="aitools">'+t('ai_used')+' '+m.tools.filter(function(x,i,a){return a.indexOf(x)===i}).map(function(x){return '<span class="tag">'+esc(t('tool_'+x))+'</span>'}).join(' ')+'</div>':'')+'</div>';
  }).join('')+(AI.busy?'<div class="aib bot thinking"><i></i><i></i><i></i> '+t('ai_think')+'</div>':'');
  log.scrollTop=log.scrollHeight;
  $('#ai-sug').hidden=ms.length>0;$('#ai-send').disabled=AI.busy;
}
function aiSend(text){
  text=(text||'').trim();if(!text||AI.busy)return;
  var mode=AI.mode,ms=AI.msgs[mode];
  ms.push({role:'user',content:text});$('#ai-in').value='';AI.busy=true;aiLog();
  api('POST','/ai/chat',{messages:ms.filter(function(m){return !m.err}).map(function(m){return {role:m.role,content:m.content}}),mode:mode,lang:lang}).then(function(r){
    ms.push({role:'assistant',content:r.reply,tools:r.tools});
  },function(e){ms.push({role:'assistant',content:errText(e),err:true});if(e.code==='ai_disabled'){AI.on=false;aiChrome()}}).then(function(){AI.busy=false;if(AI.mode===mode)aiLog()});
}
function aiBrief(force,hard){
  var mode=AI.mode==='finance'?'finance':'daily',key=mode+lang,box=$('#ai-brief');
  var c=AI.brief[key];
  function paint(r,loading){
    box.innerHTML='<div class="dhead2"><h2>'+t(mode==='finance'?'ai_brief_fin':'ai_brief_daily')+'</h2><span class="tag">'+(r&&r.ai?t('ai_ai'):t('ai_rule'))+'</span></div>'+
      (loading?'<p class="note">'+t('ai_think')+'</p>':'<div class="aimd">'+(r&&r.text?md(r.text):'<p class="empty">'+t('ai_nosig')+'</p>')+'</div>')+
      '<button type="button" class="btn ghost sm" id="ai-brief-r" style="margin-top:10px">'+t('ai_refresh')+'</button>';
  }
  if(c&&!hard&&Date.now()-c.at<300000){paint(c.r);return}
  paint(null,true);
  api('GET','/ai/brief'+Q({mode:mode,lang:lang})).then(function(r){AI.brief[key]={r:r,at:Date.now()};paint(r)},function(e){box.innerHTML='<p class="msg bad">'+esc(errText(e))+'</p>'});
}
function sevDot(s){return '<span class="sev '+s+'" title="'+t('sev_'+s)+'"></span>'}
function aiSignals(){
  var box=$('#ai-sig');
  api('GET','/ai/insights?lang='+lang).then(function(list){
    AI.sig=list;
    box.innerHTML='<div class="dhead2"><h2>'+t('ai_signals')+'</h2></div>'+(list.length?'<ul class="siglist">'+list.map(function(i){return '<li>'+sevDot(i.severity)+'<span>'+esc(i.text)+'</span></li>'}).join('')+'</ul>':'<p class="empty">'+t('ai_nosig')+'</p>');
  },function(e){box.innerHTML='<p class="msg bad">'+esc(errText(e))+'</p>'});
}

/* AI document draft */
function aiDraftUi(){
  var box=$('#ai-draft');if(!box)return;
  var can=lvl('rec')>1||lvl('inv')>1||lvl('ord')>1||lvl('bank')>1||lvl('cash')>1;
  if(!can){box.hidden=true;return}
  box.hidden=false;
  var d=AI.draft,pv='';
  if(d)pv=draftPreview(d);
  box.innerHTML='<div><h2 style="font-size:16px;font-weight:600">'+t('dr_h')+'</h2><p class="note">'+t('dr_note')+'</p></div>'+
   '<textarea id="dr-text" rows="3" maxlength="6000" placeholder="'+esc(t('dr_ph'))+'">'+esc(AI.dtext||'')+'</textarea>'+
   '<div class="pbtns"><label class="btn ghost sm" for="dr-file" style="cursor:pointer">'+svgi(NI.plus,16)+t('dr_photo')+'</label><input type="file" id="dr-file" accept="image/*" hidden><span class="note" id="dr-img">'+(AI.img?esc(AI.img.name)+' <button type="button" class="link" id="dr-clear">×</button>':'')+'</span>'+
   '<button type="button" class="btn primary sm" id="dr-make"'+(AI.dbusy?' disabled':'')+'>'+(AI.dbusy?t('dr_working'):t('dr_make'))+'</button></div><p class="msg bad" id="dr-err">'+(AI.derr?esc(AI.derr):'')+'</p>'+pv;
  $('#dr-text').addEventListener('input',function(){AI.dtext=this.value});
}
function draftOpts(list,sel,blank){
  return (blank?'<option value="">'+esc(blank)+'</option>':'')+list.map(function(o){return '<option value="'+o.id+'"'+(String(o.id)===String(sel)?' selected':'')+'>'+esc(o.name)+'</option>'}).join('');
}
function draftPreview(d){
  var mat=d.kind==='receipt',prod=d.kind==='production';
  var info=d.warnings.filter(function(w){return w.code==='unit_converted'}),bad=d.warnings.filter(function(w){return w.code!=='unit_converted'});
  var pool=(mat?MATS.map(function(m){return {id:m.id,name:m.names[lang]||m.names.en}}):PRODUCTS.map(function(n,k){return {id:PRID[k],name:n}}));
  var h='<div class="drprev"><div class="dhead2"><h2>'+t('dr_k_'+d.kind)+'</h2></div>';
  if(d.can_post){
    var parties=(d.kind==='receipt'?SUP:CUS).map(function(p){return {id:p.id,name:p.n}});
    h+='<div class="drform">';
    if(d.kind!=='production'){
      h+='<label class="fld"><span>'+t(d.kind==='receipt'?'dr_supplier':'dr_customer')+'</span><select data-dr="party">'+draftOpts(parties,d.sel.party_id,t('dr_choose'))+
         (d.party&&d.party.text?'<option value="new"'+(d.sel.party_id==='new'?' selected':'')+'>+ '+esc(t('dr_new_partner'))+': '+esc(d.party.text)+'</option>':'')+'</select></label>';
    }
    if(d.kind!=='order'){
      var whs=WH.map(function(n,i){return {id:WHID[i],name:n}}).filter(function(w,i){return prod?i<SITES.length:true});
      h+='<label class="fld"><span>'+t(prod?'dr_plant':'dr_warehouse')+'</span><select data-dr="wh">'+draftOpts(whs,d.sel.warehouse_id,t('dr_choose'))+'</select></label>';
    }
    h+='<label class="fld"><span>'+t('dr_date')+'</span><input type="date" data-dr="date" value="'+esc((d.date||'').slice(0,10))+'"></label></div>';
  }else{
    h+='<p class="note">'+[d.party?esc(d.party.name||d.party.text):'',d.account?esc(d.account.name):'',d.date?esc(d.date.slice(0,10)):''].filter(Boolean).join(' · ')+(d.amount?' · '+money(d.amount):'')+'</p>';
  }
  if(d.rows.length){
    h+='<div class="drrows">'+d.rows.map(function(r,i){
      var opts=r.candidates&&r.candidates.length?r.candidates.slice():[];
      if(r.item_id&&!opts.some(function(o){return o.id===r.item_id}))opts.unshift({id:r.item_id,name:r.name});
      var all=d.can_post?pool:opts;
      return '<div class="drrow'+(r.item_id?'':' miss')+'"><div class="drtxt"><span class="note">'+esc(r.text)+'</span>'+(r.note?'<span class="note ok">'+esc(r.note)+'</span>':'')+'</div>'+
        (d.can_post?'<select data-dr="item" data-i="'+i+'">'+draftOpts(opts.length?opts.concat(all.filter(function(o){return !opts.some(function(p){return p.id===o.id})})):all,r.item_id,t('dr_choose'))+'</select>':'<span>'+(r.item_id?esc(r.name):'—')+'</span>')+
        '<input class="num" type="number" step="any" min="0" data-dr="qty" data-i="'+i+'" value="'+(r.qty||'')+'" aria-label="'+esc(t('p_qty'))+'">'+
        (prod?'':'<input class="num" type="number" step="any" min="0" data-dr="price" data-i="'+i+'" value="'+(r.price!=null?r.price:'')+'" aria-label="'+esc(t('c_price'))+'">')+
        (r.unit?'<span class="note">'+esc(r.unit)+'</span>':'<span></span>')+'</div>';
    }).join('')+'</div>';
  }
  info.forEach(function(w){h+='<p class="note ok">'+esc(T[lang].dr_w_unit_converted.replace('%s',w.text))+'</p>'});
  bad.forEach(function(w){h+='<p class="msg bad">'+esc((T[lang]['dr_w_'+w.code]||w.code).replace('%s',w.text))+'</p>'});
  h+='<p class="msg bad" id="dr-cerr">'+(AI.cerr?esc(AI.cerr):'')+'</p>';
  h+='<div class="pbtns">'+(d.can_post?'<button type="button" class="btn primary" id="dr-create"'+(AI.cbusy?' disabled':'')+'>'+t(AI.cbusy?'dr_working':'dr_create')+'</button>':'')+
     '<button type="button" class="btn ghost" id="dr-open">'+t('dr_open')+'</button></div>';
  if(AI.cdone)h+='<p class="msg ok" id="dr-done">'+esc(t('dr_done').replace('%s',AI.cdone.number))+'</p>';
  return h+'</div>';
}
function draftSetup(d){
  d.sel={party_id:d.party&&d.party.id?d.party.id:'',warehouse_id:d.warehouse&&d.warehouse.id?d.warehouse.id:''};
  if(d.kind==='production'&&!d.sel.warehouse_id&&SITES.length===1)d.sel.warehouse_id=WHID[0];
  if(d.kind!=='production'&&!d.sel.warehouse_id&&WH.length===1)d.sel.warehouse_id=WHID[0];
  AI.cerr='';AI.cdone=null;
}
function draftChange(e){
  var el=e.target.closest('[data-dr]'),d=AI.draft;if(!el||!d)return;
  var k=el.dataset.dr,i=+el.dataset.i;
  if(k==='party')d.sel.party_id=el.value;
  else if(k==='wh')d.sel.warehouse_id=el.value?+el.value:'';
  else if(k==='date')d.date=el.value||null;
  else if(k==='item'){var r=d.rows[i];r.item_id=el.value?+el.value:null;r.name=el.options[el.selectedIndex].text;}
  else if(k==='qty')d.rows[i].qty=+el.value||0;
  else if(k==='price')d.rows[i].price=el.value===''?null:+el.value;
  if(k==='item'||k==='party')aiDraftUi();
}
function draftCreate(){
  var d=AI.draft;if(!d||AI.cbusy)return;
  var body={kind:d.kind,date:d.date||null,comment:d.comment||'',lang:lang,warehouse_id:d.sel.warehouse_id||null,
    rows:d.rows.map(function(r){return {item_id:r.item_id,qty:r.qty,price:r.price||0}})};
  if(d.sel.party_id==='new')body.new_party=d.party.text;else if(d.sel.party_id)body.party_id=+d.sel.party_id;
  AI.cerr='';AI.cbusy=true;aiDraftUi();
  api('POST','/ai/draft/commit',body).then(function(r){
    AI.cdone=r;AI.draft=null;AI.dtext='';AI.img=null;
    return Store.load();
  },function(e){AI.cerr=errText(e)}).then(function(){AI.cbusy=false;aiDraftUi()});
}
function pickImage(f){
  if(!f)return;
  var rd=new FileReader();
  rd.onload=function(){
    var im=new Image();
    im.onload=function(){
      var s=Math.min(1,1600/Math.max(im.width,im.height)),c=document.createElement('canvas');
      c.width=Math.round(im.width*s);c.height=Math.round(im.height*s);c.getContext('2d').drawImage(im,0,0,c.width,c.height);
      AI.img={name:f.name,media_type:'image/jpeg',data:c.toDataURL('image/jpeg',.85).split(',')[1]};aiDraftUi();
    };
    im.onerror=function(){AI.derr=errText({code:'bad_image'});aiDraftUi()};
    im.src=rd.result;
  };
  rd.readAsDataURL(f);
}
function aiDraft(){
  AI.dtext=$('#dr-text').value;AI.derr='';AI.dbusy=true;aiDraftUi();
  api('POST','/ai/draft',{text:AI.dtext,image:AI.img?{media_type:AI.img.media_type,data:AI.img.data}:null,lang:lang}).then(function(d){AI.draft=d;draftSetup(d)},function(e){AI.derr=errText(e);AI.draft=null}).then(function(){AI.dbusy=false;aiDraftUi()});
}
function openDraft(d){
  if(!d)return;
  var cmt=d.comment||'',pname=d.party?(d.party.name||d.party.text):'',when=d.date?new Date(d.date):null;
  function fix(sel,val){setTimeout(function(){var e=$(sel);if(e&&val)e.value=val},80)}
  function rowOf(r,mat){
    var m=MAT_IDX[r.item_id],p=PR_IDX[r.item_id];
    return {m:mat&&m!=null?m:-1,p:p!=null?p:-1,q:r.qty||0,pr:r.price||0,t:(m==null&&p==null)?r.text:''};
  }
  if(d.kind==='receipt'){
    if(!SUP.length){toast(t('dr_need_partner'),true);return}
    var si=d.party&&d.party.id!=null&&SU_IDX[d.party.id]!=null?SU_IDX[d.party.id]:0;
    rCopy={rows:d.rows.map(function(r){return rowOf(r,true)}),site:d.warehouse&&WH_IDX[d.warehouse.id]!=null?WH_IDX[d.warehouse.id]:(whIdx()[0]||0),sup:si,comment:cmt};
    location.hash='receipt-new';fix('#rcsup',pname);if(when)fix('#rcdate',toLocal(when));
  }else if(d.kind==='invoice'){
    if(!CUS.length){toast(t('dr_need_partner'),true);return}
    var ci=d.party&&d.party.id!=null&&CU_IDX[d.party.id]!=null?CU_IDX[d.party.id]:0;
    iCopy={rows:d.rows.map(function(r){return rowOf(r,false)}),site:d.warehouse&&WH_IDX[d.warehouse.id]!=null?WH_IDX[d.warehouse.id]:(whIdx()[0]||0),cus:ci,comment:cmt};
    location.hash='invoice-new';fix('#ivcus',pname);if(when)fix('#ivdate',toLocal(when));
  }else if(d.kind==='order'){
    if(!CUS.length){toast(t('dr_need_partner'),true);return}
    var oi=d.party&&d.party.id!=null&&CU_IDX[d.party.id]!=null?CU_IDX[d.party.id]:0;
    oCopy={rows:d.rows.map(function(r){return rowOf(r,false)}),cus:oi,comment:cmt};
    location.hash='order-new';fix('#odcus',pname);if(when)fix('#oddate',toDay(when));
  }else if(d.kind==='production'){
    var wi=d.sel&&d.sel.warehouse_id&&WH_IDX[d.sel.warehouse_id]!=null?WH_IDX[d.sel.warehouse_id]:0;
    pendingCopy={rows:d.rows.filter(function(r){return PR_IDX[r.item_id]!=null}).map(function(r){return {p:PR_IDX[r.item_id],q:r.qty||0}}),site:wi,comment:cmt};
    location.hash='production-new';
  }else{
    var inn=d.kind==='payment_in',acc=d.account&&AC_IDX[d.account.id]!=null?AC_IDX[d.account.id]:(accList('bank')[0]!=null?accList('bank')[0]:accList('cash')[0]);
    if(acc==null){toast(t('dr_need_partner'),true);return}
    var cu=inn&&d.party&&CU_IDX[d.party.id]!=null?CU_IDX[d.party.id]:-1,su=!inn&&d.party&&SU_IDX[d.party.id]!=null?SU_IDX[d.party.id]:-1;
    fCopy={kind:inn?'in':'out',acc:acc,art:d.article||(inn?'cust':'sup'),cus:cu,sup:su,party:(!inn&&su<0)?pname:'',to:null,amt:d.amount||0,comment:cmt};fPreset=null;
    fmode=ACC[acc].t;location.hash=fmode+'-new';
  }
}

/* ---- dashboard AI box ---- */
var BOX={at:0,key:'',r:null,sig:null};
function renderAiBox(){
  var biz=$('#biz');if(!biz||!ME)return;
  var box=$('#aibox');
  if(!box){box=document.createElement('section');box.id='aibox';box.className='panel aibox';biz.parentNode.insertBefore(box,biz.nextSibling);
    box.addEventListener('click',function(e){if(e.target.closest('a'))return});}
  var key=lang+ME.u;
  function paint(){
    var r=BOX.r,sig=(BOX.sig||[]).slice(0,4);
    box.innerHTML='<div class="dhead2"><h2>'+svgi(NI.ai,18)+' '+t('ai_box_h')+'</h2><a class="link" href="#assistant">'+t('ai_box_more')+'</a></div>'+
     (r&&r.text?'<div class="aimd">'+md(r.text)+'</div>':'')+
     (sig.length?'<ul class="siglist">'+sig.map(function(i){return '<li>'+sevDot(i.severity)+'<span>'+esc(i.text)+'</span></li>'}).join('')+'</ul>':(r&&r.text?'':'<p class="empty">'+t('ai_nosig')+'</p>'));
  }
  if(BOX.key===key&&Date.now()-BOX.at<300000){paint();return}
  box.innerHTML='<div class="dhead2"><h2>'+svgi(NI.ai,18)+' '+t('ai_box_h')+'</h2></div><p class="note">'+t('ai_think')+'</p>';
  BOX.key=key;BOX.at=Date.now();
  Promise.all([api('GET','/ai/brief'+Q({mode:(lvl('bank')||lvl('cash'))?'finance':'daily',lang:lang})).catch(function(){return null}),api('GET','/ai/insights?lang='+lang).catch(function(){return []})]).then(function(a){BOX.r=a[0];BOX.sig=a[1];paint()});
}

/* ---- reports ---- */
var REPS=[
 {id:'turnover',name:'turnover',need:['wh'],dates:1,wh:1,kind:1},
 {id:'movements',name:'movements',need:['wh'],dates:1,wh:1,kind:1,item:1,doc:1,note:'rp_note_movements'},
 {id:'sales',name:'sales',need:['inv'],dates:1,groups:['customer','item','day','month']},
 {id:'purchases',name:'purchases',need:['rec'],dates:1,groups:['supplier','item','day','month']},
 {id:'cashflow',name:'cashflow',any:['bank','cash'],dates:1,groups:['article','day','account']},
 {id:'profit',name:'profit',need:['inv','bank'],dates:1,note:'rp_note_profit'},
 {id:'plan',name:'plan',need:['prod']},
 {id:'plan_materials',name:'plan_materials',need:['prod']},
 {id:'debts_customer',name:'debts',who:'customer',need:['cus']},
 {id:'aging',name:'aging',need:['cus'],note:'rp_note_aging'},
 {id:'debts_supplier',name:'debts',who:'supplier',need:['sup']},
 {id:'forecast',name:'forecast',need:['wh'],note:'rp_note_forecast'},
 {id:'losses',name:'losses',need:['adj'],dates:1,note:'rp_note_losses'},
 {id:'production',name:'production',need:['prod'],dates:1,wh:1,groups:['item','warehouse','day','month','warehouse_item','day_item','month_item'],note:'rp_note_production'},
 {id:'scrap',name:'scrap',need:['prod'],dates:1,note:'rp_note_scrap'},
 {id:'cost',name:'cost',need:['prod','inv'],note:'rp_note_cost'},
 {id:'profit_products',name:'profit_products',need:['inv','bank'],dates:1,note:'rp_note_pprod'},
 {id:'payroll',name:'payroll',need:['pay'],dates:1,note:'rp_note_payroll'}
];
window.REPS=REPS;
/* date presets shared by the reports center and the pay statement: all time / this month / last month / this year */
var DPX={dp_all:['All time','За всё время','Barcha davr'],dp_month:['This month','Этот месяц','Shu oy'],dp_prev:['Last month','Прошлый месяц','O‘tgan oy'],dp_year:['This year','Этот год','Shu yil']};
Object.keys(DPX).forEach(function(k){T.en[k]=DPX[k][0];T.ru[k]=DPX[k][1];T.uz[k]=DPX[k][2]});
var DPK=['all','month','prev','year'];
window.dpRange=function(k){
  var n=new Date(),y=n.getFullYear(),m=n.getMonth();
  if(k==='all')return {from:'',to:''};
  if(k==='month')return {from:toDay(new Date(y,m,1)),to:toDay(n)};
  if(k==='prev')return {from:toDay(new Date(y,m-1,1)),to:toDay(new Date(y,m,0))};
  return {from:toDay(new Date(y,0,1)),to:toDay(n)};
};
window.dpActive=function(from,to){for(var i=0;i<DPK.length;i++){var r=dpRange(DPK[i]);if(r.from===(from||'')&&r.to===(to||''))return DPK[i]}return ''};
window.dpHtml=function(from,to){
  var cur=dpActive(from,to);
  return '<div class="seg" data-dps role="group" style="max-width:100%;overflow-x:auto">'+DPK.map(function(k){return '<button type="button" data-dp="'+k+'" aria-pressed="'+(cur===k)+'">'+t('dp_'+k)+'</button>'}).join('')+'</div>';
};
var RP={dinit:false,id:null,from:'',to:'',group:'',wh:'',kind:'',item:'',doc:'',data:null,err:''};
function repOk(r){return (r.need||[]).every(function(s){return lvl(s)>0})&&(!r.any||r.any.some(function(s){return lvl(s)>0}))}
function repParams(r){
  var p={lang:lang};
  if(r.dates){if(RP.from)p.start=RP.from+'T00:00:00';if(RP.to)p.end=RP.to+'T23:59:59'}
  if(r.groups)p.group=RP.group||r.groups[0];
  if(r.wh&&RP.wh)p.warehouse_id=RP.wh;if(r.kind&&RP.kind)p.kind=RP.kind;if(r.item&&RP.item)p.item_id=RP.item;if(r.doc&&RP.doc)p.doc=RP.doc;if(r.who)p.who=r.who;
  return p;
}
function renderRep(){
  var el=$('#xv-reports'),list=REPS.filter(repOk);
  if(!list.length)return;
  if(RP.id&&!list.some(function(r){return r.id===RP.id}))RP.id=null;
  if(!RP.id){
    el.innerHTML='<div class="wrap dash"><div class="dhead"><div><h1>'+t('rp_h')+'</h1><p class="note">'+t('rp_note')+'</p></div></div>'+
     '<ul class="rplist">'+list.map(function(x){return '<li><button type="button" class="rp-row" data-r="'+x.id+'"><span class="rp-t"><b>'+t('rp_'+x.id)+'</b><small>'+t('rl_'+x.id)+'</small></span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></button></li>'}).join('')+'</ul></div>';
    el.querySelector('.rplist').addEventListener('click',function(e){
      var b=e.target.closest('button[data-r]');if(!b)return;
      RP.id=b.dataset.r;RP.group='';
      if(!RP.dinit){var n=new Date();RP.from=toDay(new Date(n.getFullYear(),n.getMonth(),1));RP.to=toDay(n);RP.dinit=true}
      renderRep();window.scrollTo(0,0);
    });
    return;
  }
  var r=list.filter(function(x){return x.id===RP.id})[0];
  el.innerHTML='<div class="wrap dash"><div class="dhead"><div><button type="button" class="link back" id="rp-back">'+t('rp_h')+'</button><h1>'+t('rp_'+r.id)+'</h1></div></div>'+
   '<div class="panel stack"><div class="akbar" id="rp-bar">'+
    (r.dates?dpHtml(RP.from,RP.to):'')+
    (r.dates?'<div class="field"><label for="rp-from">'+t('rp_from')+'</label><input id="rp-from" type="date" value="'+RP.from+'"></div><div class="field"><label for="rp-to">'+t('rp_to')+'</label><input id="rp-to" type="date" value="'+RP.to+'"></div>':'')+
    (r.groups?'<div class="field"><label for="rp-group">'+t('rp_group')+'</label><select id="rp-group">'+r.groups.map(function(g){return '<option value="'+g+'"'+((RP.group||r.groups[0])===g?' selected':'')+'>'+t('g_'+g)+'</option>'}).join('')+'</select></div>':'')+
    (r.wh?'<div class="field"><label for="rp-wh">'+t('rp_wh')+'</label><select id="rp-wh"><option value="">'+t('rp_all')+'</option>'+WH.map(function(n,i){return '<option value="'+WHID[i]+'"'+(String(WHID[i])===String(RP.wh)?' selected':'')+'>'+esc(n)+'</option>'}).join('')+'</select></div>':'')+
    (r.kind?'<div class="field"><label for="rp-kind">'+t('rp_kind')+'</label><select id="rp-kind"><option value="">'+t('rp_all')+'</option><option value="product"'+(RP.kind==='product'?' selected':'')+'>'+t('k_product')+'</option><option value="material"'+(RP.kind==='material'?' selected':'')+'>'+t('k_material')+'</option></select></div>':'')+
    (r.item?'<div class="field rp-itemf"><label for="rp-item">'+t('rp_item')+'</label><input id="rp-item" type="text" data-pick="rpitem" role="combobox" aria-autocomplete="list" aria-expanded="false" autocomplete="off" spellcheck="false" placeholder="'+esc(t('rp_all')+' \u00b7 '+t('p_search'))+'" value="'+esc(RP.item?itemNameById(RP.item):'')+'"></div>':'')+
    (r.doc?'<div class="field"><label for="rp-doc">'+t('rp_doc')+'</label><select id="rp-doc"><option value="">'+t('rp_all')+'</option>'+['production','receipt','invoice','adjust'].map(function(k){return '<option value="'+k+'"'+(RP.doc===k?' selected':'')+'>'+t('rp_d_'+k)+'</option>'}).join('')+'</select></div>':'')+
    '<button type="button" class="btn ghost sm" id="rp-xlsx">'+t('rp_xlsx')+'</button></div>'+
    (r.note?'<p class="note">'+t(r.note)+'</p>':'')+'<div id="rp-out"></div></div></div>';
  $('#rp-back').addEventListener('click',function(){RP.id=null;renderRep();window.scrollTo(0,0)});
  $('#rp-bar').addEventListener('click',function(e){var b=e.target.closest('[data-dp]');if(b){var d=dpRange(b.dataset.dp);RP.from=d.from;RP.to=d.to;renderRep()}});
  $('#rp-bar').addEventListener('change',function(e){
    var id=e.target.id;if(id==='rp-from')RP.from=e.target.value;else if(id==='rp-to')RP.to=e.target.value;else if(id==='rp-group')RP.group=e.target.value;else if(id==='rp-wh')RP.wh=e.target.value;else if(id==='rp-kind')RP.kind=e.target.value;else if(id==='rp-item')return;else if(id==='rp-doc')RP.doc=e.target.value;
    repLoad(r);
  });
  var rpi=$('#rp-item');
  if(rpi){
    var rpId=function(v){var k=Object.keys(ITEM_NAME);for(var i=0;i<k.length;i++){if(ITEM_NAME[k[i]]===v)return k[i]}return null};
    rpi.addEventListener('input',function(){var v=rpi.value.trim();if(!v){if(RP.item){RP.item='';repLoad(r)}return}var id=rpId(v);if(id&&String(id)!==String(RP.item)){RP.item=id;repLoad(r)}});
    rpi.addEventListener('blur',function(){setTimeout(function(){if(pk.open&&pk.el===rpi)return;var v=rpi.value.trim();if(v&&!rpId(v))rpi.value=RP.item?itemNameById(RP.item):''},150)});
  }
  $('#rp-xlsx').addEventListener('click',function(){openBlob('/reports/center/'+r.name+'/export.xlsx'+Q(repParams(r)),r.name+'.xlsx',true)});
  repLoad(r);
}
function repLoadDoc(){
  var o=$('#rp-out');if(!o||o.dataset.doc)return;o.dataset.doc='1';
  o.addEventListener('click',function(e){
    var tr=e.target.closest('tr[data-dk]');if(!tr||RP.id!=='movements')return;
    if(window.getSelection&&String(window.getSelection()))return;
    docView(tr.dataset.dk,+tr.dataset.di,tr.dataset.dn);
  });
}
function repLoadDrill(){
  var o=$('#rp-out');if(!o||o.dataset.drill)return;o.dataset.drill='1';
  o.addEventListener('click',function(e){
    var tr=e.target.closest('tr[data-item]');if(!tr||RP.id!=='turnover')return;
    RP.id='movements';RP.item=tr.dataset.item;RP.doc='';renderRep();
  });
}

/* ---- read-only document viewer (opened from a goods-movement row) ---- */
var DVP={production:['/production','dr_k_production'],receipt:['/receipts','dv_x'],invoice:['/invoices','dv_x'],adjust:['/adjustments','dv_x']};
function docView(key,id,heading){
  var d=document.createElement('div');d.className='xmodal';d.setAttribute('role','dialog');d.setAttribute('aria-modal','true');
  d.innerHTML='<div class="xbox stack" style="width:min(720px,100%);max-height:90vh;overflow:auto"><div class="dhead2"><h2>'+esc(heading||'')+'</h2><span class="tag">'+t('dv_view_only')+'</span></div><div id="dv-body"><p class="note">…</p></div><div class="mrow"><button type="button" class="btn primary" id="dv-edit" hidden>'+t('m_edit')+'</button><button type="button" class="btn ghost" id="dv-x">'+t('dv_close')+'</button></div></div>';
  document.body.appendChild(d);
  var shut=function(){d.remove();document.removeEventListener('keydown',esc_)};
  var esc_=function(e){if(e.key==='Escape')shut()};
  document.addEventListener('keydown',esc_);
  d.addEventListener('mousedown',function(e){if(e.target===d)shut()});
  $('#dv-x').addEventListener('click',shut);$('#dv-x').focus();
  var path=(DVP[key]||[])[0];if(!path){shut();return}
  api('GET',path+'/'+id).then(function(v){
    var nm=function(i){return esc(ITEM_NAME[i]||('#'+i))};
    var wh=WHID.indexOf(v.warehouse_id),party='';
    if(v.customer_id!=null&&CU_IDX[v.customer_id]!=null)party=CUS[CU_IDX[v.customer_id]].n;
    if(v.supplier_id!=null&&SU_IDX[v.supplier_id]!=null)party=SUP[SU_IDX[v.supplier_id]].n;
    var kv=function(k,val){return val?'<div class="kv"><span>'+t(k)+'</span><b>'+esc(val)+'</b></div>':''};
    var th=function(a){return '<thead><tr>'+a.map(function(x,i){return '<th'+(i?' class="num"':'')+'>'+t(x)+'</th>'}).join('')+'</tr></thead>'};
    var td=function(a){return '<tr>'+a.map(function(x,i){return '<td'+(i?' class="num"':'')+'>'+x+'</td>'}).join('')+'</tr>'};
    var rows='',foot='';
    if(key==='production'){
      rows=th(['dv_item','dv_qty','dv_scrap'])+'<tbody>'+v.rows.map(function(r){return td([nm(r.item_id),num(r.qty,'num'),num(r.scrap||0,'num')])}).join('')+'</tbody>';
      if((v.consumption||[]).length)rows+='</table><h3 class="akhd">'+t('dv_used')+'</h3><table class="dt">'+th(['dv_item','dv_qty'])+'<tbody>'+v.consumption.map(function(c){return td([nm(c.material_id),num(c.qty,'num')])}).join('')+'</tbody>';
    }else if(key==='adjust'){
      rows=th(['dv_item','dv_sys','dv_fact','dv_diff'])+'<tbody>'+v.rows.map(function(r){return td([nm(r.item_id),num(r.system_qty,'num'),num(r.qty,'num'),num(r.delta,'num')])}).join('')+'</tbody>';
    }else{
      var tot=0;
      rows=th(['dv_item','dv_qty','dv_price','dv_sum'])+'<tbody>'+v.rows.map(function(r){var sm=r.qty*r.price;tot+=sm;return td([nm(r.item_id),num(r.qty,'num'),money(r.price),money(sm)])}).join('')+'</tbody>';
      foot='<div class="kv"><span>'+t('dv_total')+'</span><b>'+money(tot)+'</b></div>';
    }
    $('#dv-body').innerHTML=kv('dv_date',v.date?dtf(fromIso(v.date)):'')+kv('dv_wh',wh>=0?WH[wh]:'')+kv('dv_party',party)+kv('dv_comment',v.comment||'')+
      '<div class="kv"><span></span><span class="pill '+(v.status==='posted'?'posted':v.status==='deleted'?'deleted':'draft')+'">'+t('dv_status_'+(v.status||'posted'))+'</span></div>'+
      '<div style="overflow-x:auto;margin-top:8px"><table class="dt">'+rows+'</table></div>'+foot;
    var sec={production:'prod',receipt:'rec',invoice:'inv'}[key],eb=$('#dv-edit');
    if(eb&&sec&&lvl(sec)>1&&v.status!=='deleted'&&v.number){
      eb.hidden=false;
      eb.addEventListener('click',function(){
        var no=v.number,ok=key==='production'?findDoc(no):key==='receipt'?findR(no):findI(no);
        if(!ok){toast(t('rp_doc_na'),true);return}
        shut();window.RET='reports';
        if(key==='production')openEdit(no);else if(key==='receipt')openRecEdit(no);else openInvEdit(no);
      });
    }
  },function(e){$('#dv-body').innerHTML='<p class="msg bad">'+esc(errText(e))+'</p>'});
}
/* after editing a document opened from the goods movement report, go back to that report (same filters) */
window.takeRet=function(def){var r=window.RET;window.RET=null;return r||def};
window.addEventListener('hashchange',function(){var h=location.hash.slice(1);if(window.RET&&h!=='reports'&&!/-edit$/.test(h))window.RET=null});
function repLoad(r,quiet){
  var out=$('#rp-out');if(!quiet)out.innerHTML='<p class="note">…</p>';
  api('GET','/reports/center/'+r.name+Q(repParams(r))).then(function(tb){if($('#rp-out')&&RP.id===r.id)$('#rp-out').innerHTML=tableHtml(tb);if(r.id==='movements'){repLoadDoc();$('#rp-out').querySelectorAll('tbody tr').forEach(function(tr,i){var x=tb.rows[i];if(x&&x.doc_id){tr.dataset.dk=x.doc_key;tr.dataset.di=x.doc_id;tr.dataset.dn=x.doc_type+' '+x.doc;tr.style.cursor='pointer';tr.title=t('dv_open')}})}if(r.id==='turnover'){repLoadDrill();$('#rp-out').querySelectorAll('tbody tr').forEach(function(tr,i){var x=tb.rows[i];if(x&&x.item_id){tr.dataset.item=x.item_id;tr.style.cursor='pointer'}})}},function(e){if($('#rp-out'))$('#rp-out').innerHTML='<p class="msg bad">'+esc(errText(e))+'</p>'});
}

/* live updates: the reports page and the journal reload their own data (the store does not hold it) */
window.repRefresh=function(){
  var v=$('#xv-reports');if(!v||v.hidden||!RP.id||!$('#rp-out'))return;
  var r=REPS.filter(function(x){return x.id===RP.id})[0];if(r)repLoad(r,true);
};
window.audRefresh=function(){var v=$('#xv-journal');if(v&&!v.hidden&&$('#au-out'))audLoad(true)};

/* ---- journal ---- */
var AU={entity:'',action:'',user:'',from:'',to:'',rows:[],total:0,busy:false};
var ENT=['orders','invoices','receipts','production_docs','fin_docs','customers','suppliers','items','accounts','warehouses','units','users','norms'];
function changeText(x){
  var c=x.changes;if(!c)return '';
  return Object.keys(c).map(function(k){
    if(k==='rows')return t('au_rows');
    if(k==='password')return t('au_pw')+': '+c[k];
    var v=c[k];if(!Array.isArray(v))return k+': '+v;
    return k+': '+(v[0]==null||v[0]===''?'∅':v[0])+' → '+(v[1]==null||v[1]===''?'∅':v[1]);
  }).join('; ');
}
function renderAud(){
  var el=$('#xv-journal');
  if(!el.firstChild){
    el.innerHTML='<div class="wrap dash"><div class="dhead"><div><h1></h1><p class="note"></p></div></div><div class="panel stack"><div class="akbar" id="au-bar"></div><div id="au-out"></div></div></div>';
    el.addEventListener('change',function(e){
      var m={'au-e':'entity','au-a':'action','au-u':'user','au-f':'from','au-t':'to'}[e.target.id];if(!m)return;AU[m]=e.target.value;audLoad(true);
    });
    el.addEventListener('click',function(e){if(e.target.closest('#au-more'))audLoad(false)});
  }
  el.querySelector('h1').textContent=t('au_h');el.querySelector('.note').textContent=t('au_note');
  $('#au-bar').innerHTML='<div class="field"><label for="au-e">'+t('au_entity')+'</label><select id="au-e"><option value="">'+t('rp_all')+'</option>'+ENT.map(function(k){return '<option value="'+k+'"'+(AU.entity===k?' selected':'')+'>'+t('e_'+k)+'</option>'}).join('')+'</select></div>'+
   '<div class="field"><label for="au-a">'+t('au_action')+'</label><select id="au-a"><option value="">'+t('rp_all')+'</option>'+['create','update','delete','restore','login'].map(function(k){return '<option value="'+k+'"'+(AU.action===k?' selected':'')+'>'+t('a_'+k)+'</option>'}).join('')+'</select></div>'+
   '<div class="field"><label for="au-u">'+t('au_user')+'</label><input id="au-u" type="text" value="'+esc(AU.user)+'"></div>'+
   '<div class="field"><label for="au-f">'+t('rp_from')+'</label><input id="au-f" type="date" value="'+AU.from+'"></div><div class="field"><label for="au-t">'+t('rp_to')+'</label><input id="au-t" type="date" value="'+AU.to+'"></div>';
  audLoad(true);
}
function audLoad(reset){
  if(AU.busy)return;AU.busy=true;
  var q={limit:100,offset:reset?0:AU.rows.length,entity:AU.entity,action:AU.action,username:AU.user.trim().toLowerCase()};
  if(AU.from)q.start=AU.from+'T00:00:00';if(AU.to)q.end=AU.to+'T23:59:59';
  api('GET','/audit'+Q(q)).then(function(r){
    AU.rows=reset?r.rows:AU.rows.concat(r.rows);AU.total=r.total;audPaint();
  },function(e){$('#au-out').innerHTML='<p class="msg bad">'+esc(errText(e))+'</p>'}).then(function(){AU.busy=false});
}
function audPaint(){
  var out=$('#au-out');if(!out)return;
  if(!AU.rows.length){out.innerHTML='<p class="empty">'+t('rp_empty')+'</p>';return}
  out.innerHTML='<div style="overflow-x:auto"><table class="dt"><thead><tr><th>'+t('au_time')+'</th><th>'+t('au_user')+'</th><th>'+t('au_action')+'</th><th>'+t('au_entity')+'</th><th>'+t('au_changes')+'</th></tr></thead><tbody>'+
   AU.rows.map(function(x){var d=x.at?new Date(x.at.replace(' ','T')+(/[zZ]|[+-]\d\d:?\d\d$/.test(x.at)?'':'Z')):null;
    return '<tr><td class="mono">'+(d?dtf(d):'')+'</td><td>'+esc(x.user)+'</td><td>'+t('a_'+x.action)+'</td><td>'+esc((T[lang]['e_'+x.entity]||x.entity)+(x.label?' '+x.label:''))+'</td><td class="wrap" style="white-space:normal;max-width:360px">'+esc(changeText(x))+'</td></tr>'}).join('')+'</tbody></table></div>'+
   (AU.rows.length<AU.total?'<button type="button" class="btn ghost sm" id="au-more" style="margin-top:10px">'+t('au_more')+' ('+(AU.total-AU.rows.length)+')</button>':'');
}

/* ---- users ---- */
var US={rows:[],msg:null};
function premCell(u){
  if(u.role==='admin'&&u.features&&u.features.length&&!(u.premium||[]).length)return '<span class="note">'+t('us_p_always')+'</span>';
  var g=(u.premium||[]).filter(function(x){return x.feature==='meeting'})[0];
  var d=g?new Date(g.expires_at.replace(' ','T')+'Z').toLocaleDateString(LOC[lang],{day:'2-digit',month:'2-digit'}):'';
  var tip=g?(t('us_p_until')+' '+new Date(g.expires_at.replace(' ','T')+'Z').toLocaleDateString(LOC[lang])+' · '+g.uses_left+'/'+g.uses_limit+' '+t('us_p_left')):'';
  if(g&&g.active)return '<div class="pm"><span class="pmc on" title="'+esc(tip)+'">'+d+' · '+g.uses_left+'/'+g.uses_limit+'</span>'+
    '<button type="button" class="btn ghost sm pmi" data-pon="'+u.id+'" title="'+t('us_p_renew')+'" aria-label="'+t('us_p_renew')+'">↻</button>'+
    '<button type="button" class="btn ghost sm pmi" data-poff="'+u.id+'" title="'+t('us_p_off')+'" aria-label="'+t('us_p_off')+'">×</button></div>';
  return '<div class="pm">'+(g?'<span class="pmc" title="'+esc(tip)+'">'+t('us_p_end')+'</span>':'')+'<button type="button" class="btn ghost sm" data-pon="'+u.id+'" title="'+t('us_p_on')+'">'+t('us_p_on_s')+'</button></div>';
}
var ROLE_IDS=['admin','director','prod','wh','sales','acc'];
function renderUsr(){
  var el=$('#xv-users'),edit=lvl('set')>1;
  api('GET','/auth/users').then(function(rows){
    US.rows=rows;
    el.innerHTML='<div class="wrap dash"><div class="dhead"><div><h1>'+t('us_h')+'</h1><p class="note">'+t('us_note')+'</p></div></div>'+
     '<div class="panel stack"><div style="overflow-x:auto"><table class="dt ut"><thead><tr><th>'+t('us_name')+'</th><th>'+t('us_login')+'</th><th>'+t('us_role')+'</th><th>'+t('us_active')+'</th>'+(ME&&ME.owner?'<th>'+t('us_prem')+'</th>':'')+(edit?'<th>'+t('us_reset')+'</th><th></th>':'')+'</tr></thead><tbody>'+
     rows.map(function(u){
       if(!edit)return '<tr><td>'+esc(u.full_name)+'</td><td class="mono">'+esc(u.username)+'</td><td>'+t('role_'+u.role)+'</td><td>'+(u.is_active?'✓':t('us_off'))+'</td>'+(ME&&ME.owner?'<td>'+((u.features||[]).indexOf('meeting')>=0?'✓':'')+'</td>':'')+'</tr>';
       return '<tr data-u="'+u.id+'"><td><input type="text" data-f="name" value="'+esc(u.full_name)+'"></td><td class="mono">'+esc(u.username)+'</td><td><select data-f="role">'+ROLE_IDS.map(function(r){return '<option value="'+r+'"'+(r===u.role?' selected':'')+'>'+t('role_'+r)+'</option>'}).join('')+'</select></td>'+
        '<td><input type="checkbox" data-f="act"'+(u.is_active?' checked':'')+'></td>'+(ME&&ME.owner?'<td>'+(u.is_owner?'<span class="note">'+t('us_p_always')+'</span>':premCell(u))+'</td>':'')+'<td><input type="password" data-f="pw" autocomplete="new-password" placeholder="••••••••"></td><td><button type="button" class="btn ghost sm" data-save="'+u.id+'">'+t('us_save')+'</button>'+(u.totp_enabled?' <button type="button" class="btn ghost sm" data-r2="'+u.id+'">'+t('us_reset2fa')+'</button>':'')+'</td></tr>';
     }).join('')+'</tbody></table></div><p class="msg" id="us-msg"></p></div>'+
     (edit?'<div class="panel stack"><h2>'+t('us_add')+'</h2><div class="akbar"><div class="field"><label for="nu-name">'+t('us_name')+'</label><input id="nu-name" type="text"></div><div class="field"><label for="nu-login">'+t('us_login')+'</label><input id="nu-login" type="text" autocomplete="off"></div>'+
       '<div class="field"><label for="nu-role">'+t('us_role')+'</label><select id="nu-role">'+ROLE_IDS.map(function(r){return '<option value="'+r+'">'+t('role_'+r)+'</option>'}).join('')+'</select></div><div class="field"><label for="nu-pw">'+t('us_pw')+'</label><input id="nu-pw" type="password" autocomplete="new-password"></div>'+
       '<button type="button" class="btn primary sm" id="nu-add">'+t('us_add')+'</button></div></div>':'')+'</div>';
    var msg=function(txt,bad){var m=$('#us-msg');if(m){m.className='msg '+(bad?'bad':'ok');m.textContent=txt}};
    el.onclick=function(e){
      var s=e.target.closest('[data-save]');
      if(s){var tr=s.closest('tr'),body={full_name:tr.querySelector('[data-f=name]').value,role:tr.querySelector('[data-f=role]').value,is_active:tr.querySelector('[data-f=act]').checked},pw=tr.querySelector('[data-f=pw]').value;if(pw)body.password=pw;
        api('PATCH','/auth/users/'+s.dataset.save,body).then(function(){msg(t('us_saved'));tr.querySelector('[data-f=pw]').value=''},function(er){msg(errText(er),true)});return}
      var po=e.target.closest('[data-pon],[data-poff]');
      if(po){var on=po.hasAttribute('data-pon');api('PATCH','/auth/users/'+(po.dataset.pon||po.dataset.poff),{premium:{feature:'meeting',on:on}}).then(function(){renderUsr()},function(er){msg(errText(er),true)});return}
      var r2=e.target.closest('[data-r2]');
      if(r2){api('PATCH','/auth/users/'+r2.dataset.r2,{reset_2fa:true}).then(function(){msg(t('us_2fa_reset'));renderUsr()},function(er){msg(errText(er),true)});return}
      if(e.target.closest('#nu-add')){
        api('POST','/auth/users',{username:$('#nu-login').value,password:$('#nu-pw').value,full_name:$('#nu-name').value,role:$('#nu-role').value}).then(function(){renderUsr()},function(er){msg(errText(er),true)});
      }
    };
  },function(e){el.innerHTML='<div class="wrap dash"><p class="msg bad">'+esc(errText(e))+'</p></div>'});
}


/* ---- security: password, two-factor sign-in, signed-in browsers ---- */
function renderSec(){
  var el=$('#xv-security');
  Promise.all([api('GET','/auth/me'),api('GET','/auth/sessions'),api('GET','/telegram').catch(function(){return {enabled:false}})]).then(function(r){
    var me=r[0],ss=r[1],tgs=r[2],h='<div class="wrap dash"><div class="dhead"><div><h1>'+t('sc_h')+'</h1><p class="note">'+t('sc_note')+'</p></div></div>';
    if(me.must_setup_2fa)h+='<div class="aioff"><b>'+t('sc_must')+'</b></div>';
    h+='<div class="panel stack"><h2>'+t('sc_pw')+'</h2><p class="note">'+t('sc_pw_note')+'</p><div class="pbtns"><button type="button" class="btn ghost sm" id="sc-pw">'+t('pw_btn')+'</button></div></div>';
    h+='<div class="panel stack" id="sc-2fa"><h2>'+t('sc_2fa')+'</h2><p class="note">'+t(me.totp_enabled?'sc_2fa_on':'sc_2fa_off')+'</p>';
    if(me.totp_enabled&&!me.must_setup_2fa)h+='<form class="akbar" id="sc-off"><div class="field"><label for="sc-offpw">'+t('sc_off_pw')+'</label><input id="sc-offpw" type="password" autocomplete="current-password"></div><div class="field"><label for="sc-offc">'+t('sc_code')+'</label><input id="sc-offc" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="7"></div><button type="submit" class="btn ghost sm">'+t('sc_off_btn')+'</button></form>';
    else if(!me.totp_enabled)h+='<div class="pbtns"><button type="button" class="btn primary sm" id="sc-on">'+t('sc_2fa_start')+'</button></div><div id="sc-setup"></div>';
    h+='<p class="msg" id="sc-m2"></p></div>';
    if(tgs.enabled||tgs.linked){
      h+='<div class="panel stack" id="sc-tg"><h2>'+t('tg_h')+'</h2><p class="note">'+t(tgs.linked?'tg_on':'tg_off')+'</p>';
      if(tgs.linked)h+='<div class="pbtns"><button type="button" class="btn ghost sm" id="tg-off">'+t('tg_unlink')+'</button></div>';
      else h+='<div class="pbtns"><button type="button" class="btn primary sm" id="tg-code">'+t('tg_code')+'</button></div><div id="tg-box"></div>';
      h+='<p class="msg" id="sc-m4"></p></div>';
    }
    h+='<div class="panel stack"><div class="dhead2"><h2>'+t('sc_sess')+'</h2>'+(ss.length>1?'<button type="button" class="btn ghost sm" id="sc-all">'+t('sc_out_all')+'</button>':'')+'</div><p class="note">'+t('sc_sess_note')+'</p><ul class="bl">'+
      ss.map(function(x){return '<li><div class="r1"><span><b>'+esc(shortAgent(x.agent))+'</b>'+(x.current?' <span class="tag">'+t('sc_this')+'</span>':'')+'<br><small class="note">'+esc(x.ip||'')+' · '+t('sc_seen')+' '+esc(shortWhen(x.last_seen))+' · '+t('sc_since')+' '+esc(shortWhen(x.created_at))+'</small></span>'+(x.current?'':'<button type="button" class="btn ghost sm" data-rv="'+esc(x.id)+'">'+t('sc_out')+'</button>')+'</div></li>'}).join('')+'</ul><p class="msg" id="sc-m3"></p></div></div>';
    el.innerHTML=h;
    if(me.must_setup_2fa&&me.totp_enabled===false)setTimeout(function(){var b=$('#sc-on');if(b)b.focus()},50);
    var say=function(id,txt,bad){var m=$(id);if(m){m.className='msg '+(bad?'bad':'ok');m.textContent=txt}};
    $('#sc-pw').onclick=pwDialog;
    var on=$('#sc-on');
    if(on)on.onclick=function(){
      api('POST','/auth/2fa/setup').then(function(s){
        $('#sc-setup').innerHTML='<p class="note">'+t('sc_2fa_scan')+'</p><div class="qrbox">'+s.qr_svg+'</div><p class="note">'+t('sc_2fa_key')+' <code class="mono">'+esc(s.secret.replace(/(.{4})/g,'$1 ').trim())+'</code></p><form class="akbar" id="sc-en"><div class="field"><label for="sc-c">'+t('sc_code')+'</label><input id="sc-c" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="7"></div><button type="submit" class="btn primary sm">'+t('sc_confirm')+'</button></form>';
        on.hidden=true;$('#sc-c').focus();
        $('#sc-en').onsubmit=function(e){e.preventDefault();api('POST','/auth/2fa/enable',{code:$('#sc-c').value}).then(function(){
          if(ME)ME.must2fa=false;toast(t('sc_2fa_done'));renderSec()},function(er){say('#sc-m2',errText(er),true)})};
      },function(er){say('#sc-m2',errText(er),true)});
    };
    var tgc=$('#tg-code');
    if(tgc)tgc.onclick=function(){api('POST','/telegram/code').then(function(c){
      $('#tg-box').innerHTML='<p class="note">'+t('tg_steps')+'</p><p><code class="mono" style="font-size:22px;letter-spacing:.12em">'+esc(c.code)+'</code></p><p class="note">'+(c.username?'<a href="https://t.me/'+esc(c.username)+'" target="_blank" rel="noopener">@'+esc(c.username)+'</a> · ':'')+'/start '+esc(c.code)+' · '+t('tg_valid')+'</p>';
    },function(er){say('#sc-m4',errText(er),true)})};
    var tgo=$('#tg-off');
    if(tgo)tgo.onclick=function(){api('DELETE','/telegram').then(function(){toast(t('tg_gone'));renderSec()},function(er){say('#sc-m4',errText(er),true)})};
    var off=$('#sc-off');
    if(off)off.onsubmit=function(e){e.preventDefault();api('POST','/auth/2fa/disable',{password:$('#sc-offpw').value,code:$('#sc-offc').value}).then(function(){toast(t('sc_2fa_gone'));renderSec()},function(er){say('#sc-m2',errText(er),true)})};
    el.onclick=function(e){
      var b=e.target.closest('[data-rv]');
      if(b){api('DELETE','/auth/sessions/'+b.dataset.rv).then(function(){toast(t('sc_out_ok'));renderSec()},function(er){say('#sc-m3',errText(er),true)});return}
      if(e.target.closest('#sc-all'))api('POST','/auth/sessions/revoke-others').then(function(){toast(t('sc_out_ok'));renderSec()},function(er){say('#sc-m3',errText(er),true)});
    };
  },function(e){el.innerHTML='<div class="wrap dash"><p class="msg bad">'+esc(errText(e))+'</p></div>'});
}
function shortAgent(a){
  a=a||'';var br=/(Edg|OPR|Firefox|Chrome|Safari)\//.exec(a),os=/(Windows|Android|iPhone|iPad|Mac OS X|Linux)/.exec(a);
  var b=br?({Edg:'Edge',OPR:'Opera'}[br[1]]||br[1]):'',o=os?os[1].replace('Mac OS X','macOS'):'';
  return (b&&o?b+' · '+o:b||o||'—');
}
function shortWhen(iso){
  var d=new Date(String(iso).replace(' ','T')+(/[zZ]|[+-]\d\d:?\d\d$/.test(iso)?'':'Z'));
  if(isNaN(d))return '';
  return pad2(d.getDate())+'.'+pad2(d.getMonth()+1)+' '+pad2(d.getHours())+':'+pad2(d.getMinutes());
}

/* ---- my password (dialog opened from the sidebar) ---- */
function pwDialog(){
  var d=document.createElement('div');d.className='xmodal';d.setAttribute('role','dialog');d.setAttribute('aria-modal','true');
  d.innerHTML='<form class="xbox stack"><h2>'+t('pw_h')+'</h2><div class="field"><label for="pw-o">'+t('pw_old')+'</label><input id="pw-o" type="password" autocomplete="current-password"></div><div class="field"><label for="pw-n">'+t('pw_new')+'</label><input id="pw-n" type="password" autocomplete="new-password"></div><p class="msg" id="pw-m"></p><div class="pbtns"><button class="btn primary sm" type="submit">'+t('pw_btn')+'</button><button type="button" class="btn ghost sm" id="pw-x">'+t('close')+'</button></div></form>';
  document.body.appendChild(d);$('#pw-o').focus();
  var shut=function(){d.remove()};
  d.addEventListener('mousedown',function(e){if(e.target===d)shut()});
  d.addEventListener('keydown',function(e){if(e.key==='Escape')shut()});
  $('#pw-x').addEventListener('click',shut);
  d.querySelector('form').addEventListener('submit',function(e){
    e.preventDefault();
    api('POST','/auth/password',{old_password:$('#pw-o').value,new_password:$('#pw-n').value}).then(function(){toast(t('pw_ok'));shut()},function(er){var m=$('#pw-m');m.className='msg bad';m.textContent=errText(er)});
  });
}
var BRAND_MARK='<svg class="logo" role="img" aria-label="Prime Beton"><use href="#pb-logo"/></svg>';
var _bs=buildSide;
buildSide=function(){var oldMe=$('#mepanel');if(oldMe)oldMe.remove();_bs();var sd=$('#side');if(sd&&!sd.querySelector('.sbrand'))sd.insertAdjacentHTML('afterbegin','<a class="sbrand" href="#'+homeHash()+'">'+BRAND_MARK+'</a>');var me=document.querySelector('#side .me');if(me&&!$('#pwbtn')){var b=document.createElement('button');b.type='button';b.className='ibtn';b.id='pwbtn';b.innerHTML=svgi(NI.key);b.title=b.ariaLabel=t('pw_h');b.addEventListener('click',pwDialog);me.insertBefore(b,$('#signout'))}placeMe()};
/* the user panel: top bar (right side) on wide screens, bottom of the drawer on narrow ones */
var WIDE=window.matchMedia('(min-width:960px)');
function placeMe(){
  var me=$('#mepanel')||document.querySelector('#side .me'),tools=document.querySelector('.top .tools'),sd=$('#side');
  if(!me||!tools||!sd)return;
  me.id='mepanel';
  if(!ME){me.remove();return}
  if(WIDE.matches){if(me.parentNode!==tools)tools.appendChild(me)}else if(me.parentNode!==sd)sd.appendChild(me);
}
(WIDE.addEventListener?WIDE.addEventListener('change',placeMe):WIDE.addListener(placeMe));

/* ---- PDF buttons on existing screens ---- */
(function(){
  var pb=document.querySelector('#iv-view .pbtns');
  if(pb){var b=document.createElement('button');b.type='button';b.className='btn ghost sm';b.id='ivvpdf';b.setAttribute('data-i18n','pdf_print');b.textContent='PDF';pb.appendChild(b);
    b.addEventListener('click',function(){var v=findI(IS.view);if(v)openBlob('/reports/print/invoice/'+v.id+'.pdf?lang='+lang,v.no+'.pdf')})}
  var ab=document.querySelector('#cu-akt .akbar');
  if(ab){var c=document.createElement('button');c.type='button';c.className='btn ghost sm';c.id='akpdf';c.setAttribute('data-i18n','pdf_print');c.textContent='PDF';ab.appendChild(c);
    c.addEventListener('click',function(){
      if(AK.cus<0)return;var p={lang:lang},f=$('#akfrom').value,to=$('#akto').value;
      if(f)p.start=f+'T00:00:00';if(to)p.end=to+'T23:59:59';
      if(AK.sup)p.supplier_id=SUP[AK.cus].id;else p.customer_id=CUS[AK.cus].id;
      openBlob('/reports/print/statement.pdf'+Q(p),'statement.pdf');
    })}
})();

/* repaint language-dependent screens */
var _al=applyLang;
applyLang=function(){_al();
  var h=(location.hash||'').replace('#','');
  if(ME&&VIEWS.indexOf(h)>-1){try{RENDER[h]()}catch(e){}}
  if(ME&&h==='dashboard'){BOX.at=0;try{renderAiBox()}catch(e){}}
};
})();
