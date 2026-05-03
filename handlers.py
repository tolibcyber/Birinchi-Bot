import sqlite3
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboard import *
from database import add_user, get_candidates, get_top_candidates, ADMIN_ID, get_setting, set_setting, get_stats

router = Router()
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}

# Admin uchun holatlar
class AdminStates(StatesGroup):
    waiting_for_channel = State()

# Obunani tekshirish funksiyasi
async def is_subscribed(bot, user_id):
    channel = get_setting('channel')
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# --- START HANDLER ---
@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)
    
    # Oylik foydalanuvchi statistikasini profilga chiqarish
    total, monthly = get_stats()
    try:
        await message.bot.set_my_short_description(f"🎁 {monthly:,} oylik foydalanuvchi!")
    except: pass

    # 1. OBUNA TEKSHIRUV (STARTDA)
    if not await is_subscribed(message.bot, user_id):
        current_channel = get_setting('channel')
        sub_text = (
            f"👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>\n\n"
            f"Botimizga xush kelibsiz! Botdan to'liq foydalanish, turli qiziqarli o'yinlarda qatnashish "
            f"va sovrinli konkurslarda ishtirok etish uchun avval kanalimizga a'zo bo'lishingiz lozim.\n\n"
            f"📢 <b>Kanalimiz:</b> {current_channel}\n\n"
            f"<i>Obuna bo'lgach, 'Obunani tekshirish' tugmasini bosing yoki qayta /start buyrug'ini yuboring.</i>"
        )
        return await message.answer(sub_text, reply_markup=sub_keyboard(current_channel), parse_mode="HTML")
    
    # 2. OVOZ BERISH LOGIKASI
    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        
        if not await is_subscribed(message.bot, user_id):
            return await message.answer(
                f"⚠️ @{candidate}ga ovoz berish uchun avval kanalga a'zo bo'ling!", 
                reply_markup=sub_keyboard(get_setting('channel'))
            )
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        try:
            # AVVAL TEKSHIRAMIZ: Foydalanuvchi umuman biron marta ovoz berganmi?
            cursor.execute("SELECT candidate_username FROM votes WHERE user_id = ?", (user_id,))
            already_voted = cursor.fetchone()

            if already_voted:
                # Agar allaqachon ovoz bergan bo'lsa, xabar beramiz va to'xtatamiz
                await message.answer("🚫 Siz allaqachon ovoz bergansiz! Faqat bir marta ovoz berish imkoniyati mavjud.")
                return

            # Agar ovoz bermagan bo'lsa, bazaga yozamiz
            cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
            cursor.execute("UPDATE candidates SET votes_count = votes_count + 1 WHERE username = ?", (candidate,))
            conn.commit()
            
            await message.answer(f"✅ Rahmat! @{candidate} uchun ovozingiz muvaffaqiyatli qabul qilindi.")
            
            if LAST_BATTLE_POST["message_id"]:
                candidates = get_candidates()
                bot_info = await message.bot.get_me()
                try:
                    await message.bot.edit_message_reply_markup(
                        chat_id=LAST_BATTLE_POST["chat_id"],
                        message_id=LAST_BATTLE_POST["message_id"],
                        reply_markup=get_battle_kb(candidates, bot_info.username)
                    )
                except: pass

        except sqlite3.Error as e:
            # Bazaviy xatoliklar uchun (masalan, baza yopiq bo'lsa)
            await message.answer("⚠️ Tizimda xatolik yuz berdi, keyinroq urinib ko'ring.")
        finally: 
            conn.close()
        return
    
    # ASOSIY MENYU XABARI
    start_txt = (
        f"👋 <b>Salom {message.from_user.first_name}!</b>\n\n"
        f"Sizni botimizda ko'rib turganimizdan xursandmiz! Bu yerda siz quyidagi imkoniyatlarga egasiz:\n\n"
        f"🎡 <b>Baraban:</b> O'z omadingizni sinab ko'ring va sovg'alar yuting!\n"
        f"✌️ <b>Enik-Benik:</b> Do'stlar bilan qiziqarli o'yinlar o'ynang!\n"
        f"🎤 <b>Ovozli Batl:</b> O'z kanalingizda professional konkurslar tashkil qiling!\n\n"
        f"🚀 <b>Pastdagi menyudan o'zingizga kerakli bo'limni tanlang:</b>"
    )
    await message.answer(start_txt, reply_markup=main_menu(user_id, ADMIN_ID), parse_mode="HTML")

# --- OVOZLI BATL BO'LIMI ---
@router.callback_query(F.data == "voice_battle")
async def voice_battle_handler(callback: types.CallbackQuery):
    await callback.answer()
    bot_info = await callback.bot.get_me()
    guide_text = (
        f"🎤 <b>Ovozli Batl (Konkurs) tashkil qilish bo'yicha to'liq qo'llanma:</b>\n\n"
        f"O'z kanalingizda professional darajadagi ovozli batllarni o'tkazish juda oson!\n\n"
        f"1️⃣ <b>Botni kanalga qo'shish:</b> Pastdagi tugma orqali botni o'z kanalingizga qo'shing va unga <b>Admin</b> huquqini bering.\n\n"
        f"2️⃣ <b>Konkursni boshlash:</b> Bot admin bo'lgan kanalingizga <code>#konkursx</code> kalit so'zini yuboring.\n\n"
        f"3️⃣ <b>Avtomatik post:</b> Bot darhol kanalga chiroyli dizayndagi konkurs postini joylashtiradi.\n\n"
        f"⚠️ <b>Muhim eslatma:</b> Ishtirokchilar 'Qatnashish' tugmasini bosish orqali avtomatik ro'yxatga qo'shiladi va ularga maxsus ovoz berish havolasi beriladi.\n\n"
        f"💎 <b>Botning afzalligi:</b> Har bir ovoz beruvchi majburiy obunadan o'tadi, bu esa kanalingizni tez o'stiradi!"
    )
    await callback.message.edit_text(
        text=guide_text, 
        reply_markup=voice_battle_kb(bot_info.username), 
        parse_mode="HTML"
    )

# --- ADMIN PANEL ---
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: types.CallbackQuery):
    if str(callback.from_user.id) != str(ADMIN_ID): return
    await callback.answer()
    await callback.message.edit_text(
        "🛠 <b>Admin Panelga xush kelibsiz!</b>\n\n"
        "Bu yerdan majburiy obuna kanalini boshqarishingiz va bot statistikasini ko'rishingiz mumkin:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "change_channel")
async def change_channel_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📝 Yangi majburiy obuna kanali usernamesini yuboring (masalan: @KanalNomi):")
    await state.set_state(AdminStates.waiting_for_channel)

@router.message(AdminStates.waiting_for_channel)
async def process_channel_update(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != str(ADMIN_ID): return
    new_channel = message.text.strip()
    if new_channel.startswith("@"):
        set_setting('channel', new_channel)
        await message.answer(f"✅ Majburiy obuna kanali muvaffaqiyatli {new_channel}ga o'zgartirildi!")
        await state.clear()
    else:
        await message.answer("❌ Xato! Kanal username @ belgisi bilan boshlanishi kerak.")

@router.callback_query(F.data == "bot_strategy")
async def bot_strategy_handler(callback: types.CallbackQuery):
    total, monthly = get_stats()
    strategy_text = (
        f"📊 <b>Bot Strategiyasi va Statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total} ta</b>\n"
        f"🔥 Oylik foydalanuvchilar: <b>{monthly} ta</b>\n"
        f"📢 Joriy kanal: <b>{get_setting('channel')}</b>\n\n"
        f"💡 <b>Strategiya:</b> Bot o'yinlar va ovozli batllar orqali trafikni ushlaydi. "
        f"Har bir ovoz jarayoni majburiy obuna orqali kanal o'sishini ta'minlaydi."
    )
    await callback.message.answer(strategy_text, parse_mode="HTML")
    await callback.answer()

# --- BOSHQA FUNKSIYALAR ---
@router.callback_query(F.data == "enik_benik")
async def enik_benik_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("🎮 Enik-Benik o'yini tez kunda qo'shiladi...")

@router.message(F.text == "📊 Natijalar")
async def ask_admin_top(message: types.Message):
    # ADMIN_ID o'rniga o'zingni raqamingni yozishni unutma
    if message.from_user.id != ADMIN_ID: 
        return 
    
    await message.answer(
        "📊 <b>Natijalarni qanday ko'rinishda chiqarmoqchisiz?</b>\n"
        "Tanlovni amalga oshiring 👇", 
        parse_mode="HTML",
        reply_markup=get_admin_results_kb()
    )

@router.callback_query(lambda c: c.data.startswith('show_top_'))
async def process_admin_results(callback_query: types.CallbackQuery):
    # Callbackdan 5 yoki 10 raqamini ajratib olamiz
    limit = int(callback_query.data.split('_')[2])
    
    # database.py dagi yangi funksiyamizni chaqiramiz
    results = get_top_candidates(limit)
    
    if not results:
        await callback_query.answer("Hozircha ishtirokchilar yo'q!", show_alert=True)
        return

    header = f"📊 <b>TOP {limit} NATIJALAR</b>\n🏆 <b>Eng kuchli kurashchilar</b>🥳\n\n"
    
    body = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (username, count) in enumerate(results):
        medal = medals[i] if i < len(medals) else "👤"
        # Rasmdagi chiroyli dizayn (blockquote)
        body += f"<blockquote>{medal} @{username} — <b>{count} ta ovoz</b> </blockquote>\n\n"

    footer = "🎁 <b>Konkurs davom etmoqda...</b>"
    
    await callback_query.message.edit_text(
        header + body + footer, 
        parse_mode="HTML"
    )
    await callback_query.answer()

# --- QATNASHISH TUGMASI (TO'G'RILANDI) ---
@router.callback_query(F.data == "join_contest")
async def join_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Obuna tekshiruvi
    if not await is_subscribed(callback.bot, user_id):
        await callback.answer("⚠️ Avval kanalga a'zo bo'ling!", show_alert=True)
        return await callback.message.answer(
            "Konkursda qatnashish uchun kanalga a'zo bo'ling:", 
            reply_markup=sub_keyboard(get_setting('channel'))
        )

    user_username = callback.from_user.username
    if not user_username:
        return await callback.answer("❌ Xatolik: Profilingizda username bo'lishi shart!", show_alert=True)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username) VALUES (?)", (user_username,))
        conn.commit()
        await callback.answer("✅ Siz muvaffaqiyatli ro'yxatga qo'shildingiz!", show_alert=True)
        
        # Postni yangilash
        if LAST_BATTLE_POST["message_id"]:
            candidates = get_candidates()
            bot_info = await callback.bot.get_me()
            try:
                await callback.bot.edit_message_reply_markup(
                    chat_id=LAST_BATTLE_POST["chat_id"],
                    message_id=LAST_BATTLE_POST["message_id"],
                    reply_markup=get_battle_kb(candidates, bot_info.username)
                )
            except: pass
            
    except sqlite3.IntegrityError:
        await callback.answer("😊 Siz allaqachon ro'yxatdasiz.", show_alert=True)
    finally: conn.close()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_results_kb():
    buttons = [
        [InlineKeyboardButton(text="🔝 TOP 5", callback_data="show_top_5")],
        [InlineKeyboardButton(text="🔝 TOP 10", callback_data="show_top_10")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- KANALGA POST YUBORISH (#konkursx) ---
@router.message(F.text.contains("#konkursx"))
@router.channel_post(F.text.contains("#konkursx"))
async def start_konkurs_handler(message: types.Message):
    bot_info = await message.bot.get_me()
    candidates = get_candidates()
    battle_text = (
        "🏆 <b>KONKURS BOSHLANDI!</b> 🥳\n\n"
        "❕ <b>Shartlar:</b> Quyidagi kanalga obuna bo'lish va "
        "o'z yaqinlaringizdan ovoz yig'ish.\n\n"
        "🚫 <b>Diqqat:</b> Agar ovoz beruvchi kanaldan chiqib ketsa, uning ovozi avtomatik tarzda bekor qilinadi!\n\n"
        "➕ <b>Konkursga qo'shilish uchun pastdagi tugmani bosing:</b> 👇"
    )
    sent_post = await message.answer(
        battle_text, 
        reply_markup=get_battle_kb(candidates, bot_info.username), 
        parse_mode="HTML"
    )
    LAST_BATTLE_POST["chat_id"] = sent_post.chat.id
    LAST_BATTLE_POST["message_id"] = sent_post.message_id
    try: await message.delete()
    except: pass

@router.callback_query(F.data == "back_to_main")
async def back_home(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(text="Kerakli bo'limni tanlang:", reply_markup=main_menu(callback.from_user.id, ADMIN_ID))

@router.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    if await is_subscribed(callback.bot, callback.from_user.id):
        await callback.answer("✅ Rahmat, obuna tasdiqlandi!", show_alert=True)
        await callback.message.delete()
        await callback.message.answer("Xush kelibsiz! Endi botdan foydalanishingiz mumkin:", reply_markup=main_menu(callback.from_user.id, ADMIN_ID))
    else:
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)
