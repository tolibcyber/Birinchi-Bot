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

class AdminStates(StatesGroup):
    waiting_for_channel = State()

# --- BAZANI TOZALASH FUNKSIYASI ---
def reset_contest():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM votes")
    conn.commit()
    conn.close()

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
    
    total, monthly = get_stats()
    try:
        await message.bot.set_my_short_description(f"🎁 {monthly:,} oylik foydalanuvchi!")
    except: pass

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
            cursor.execute("SELECT candidate_username FROM votes WHERE user_id = ?", (user_id,))
            already_voted = cursor.fetchone()

            if already_voted:
                await message.answer("🚫 Siz allaqachon ovoz bergansiz! Faqat bir marta ovoz berish imkoniyati mavjud.")
                return

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
        except sqlite3.Error:
            await message.answer("⚠️ Tizimda xatolik yuz berdi, keyinroq urinib ko'ring.")
        finally: conn.close()
        return
    
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
    await callback.message.edit_text(text=guide_text, reply_markup=voice_battle_kb(bot_info.username), parse_mode="HTML")

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

# --- NATIJALAR QISMI ---
def get_admin_results_kb():
    buttons = [
        [InlineKeyboardButton(text="🔝 TOP 5", callback_data="show_top_5")],
        [InlineKeyboardButton(text="🔝 TOP 10", callback_data="show_top_10")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "📊 Natijalar")
async def ask_admin_top(message: types.Message):
    if message.from_user.id != ADMIN_ID: return 
    await message.answer(
        "📊 <b>Natijalarni qanday ko'rinishda chiqarmoqchisiz?</b>\n"
        "Tanlovni amalga oshiring 👇", 
        parse_mode="HTML",
        reply_markup=get_admin_results_kb()
    )

@router.callback_query(lambda c: c.data.startswith('show_top_'))
async def process_admin_results(callback_query: types.CallbackQuery):
    limit = int(callback_query.data.split('_')[2])
    results = get_top_candidates(limit)
    
    if not results:
        await callback_query.answer("Hozircha ishtirokchilar yo'q!", show_alert=True)
        return

    header = f"📊 <b>TOP {limit} NATIJALAR</b>\n🏆 <b>Eng kuchli kurashchilar</b>🥳\n\n"
    body = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (username, count) in enumerate(results):
        medal = medals[i] if i < len(medals) else "👤"
        body += f"<blockquote>{medal} @{username} — <b>{count} ta ovoz</b> </blockquote>\n\n"

    await callback_query.message.edit_text(header + body + "🎁 <b>Konkurs davom etmoqda...</b>", parse_mode="HTML")
    await callback_query.answer()

# --- QATNASHISH TUGMASI ---
@router.callback_query(F.data == "join_contest")
async def join_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await is_subscribed(callback.bot, user_id):
        await callback.answer("⚠️ Avval kanalga a'zo bo'ling!", show_alert=True)
        return

    user_username = callback.from_user.username
    if not user_username:
        return await callback.answer("❌ Xatolik: Profilingizda username bo'lishi shart!", show_alert=True)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username) VALUES (?)", (user_username,))
        conn.commit()
        await callback.answer("✅ Siz muvaffaqiyatli ro'yxatga qo'shildingiz!", show_alert=True)
        
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

# --- KANALGA POST (#konkursx) ---
@router.message(F.text.contains("#konkursx"))
@router.channel_post(F.text.contains("#konkursx"))
async def start_konkurs_handler(message: types.Message):
    reset_contest() # Eski ovozlarni o'chirish
    bot_info = await message.bot.get_me()
    candidates = []
    
    battle_text = (
        "🏆 <b>KONKURS BOSHLANDI!</b> 🥳\n\n"
        "❕ <b>Shartlar:</b> Quyidagi kanalga obuna bo'lish va "
        "o'z yaqinlaringizdan ovoz yig'ish.\n\n"
        "<blockquote>🚫 <b>Diqqat:</b> Agar ovoz beruvchi kanaldan chiqib ketsa, uning ovozi avtomatik tarzda bekor qilinadi!</blockquote>\n\n"
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

# --- QOLGAN STANDART HANDLERLAR ---
@router.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: types.CallbackQuery):
    if await is_subscribed(callback.bot, callback.from_user.id):
        await callback.answer("✅ Rahmat, obuna tasdiqlandi!", show_alert=True)
        await callback.message.delete()
        await callback.message.answer("Xush kelibsiz! Endi botdan foydalanishingiz mumkin:", reply_markup=main_menu(callback.from_user.id, ADMIN_ID))
    else:
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_home(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(text="Kerakli bo'limni tanlang:", reply_markup=main_menu(callback.from_user.id, ADMIN_ID))
